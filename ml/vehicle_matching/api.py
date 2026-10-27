"""Isolated v2 experiment. The original v1 server is unchanged."""
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dataclasses import replace
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException

from recommender.api import problem
from vehicle_matching.catalog import ROOT, catalog_fingerprint, read_catalog
from vehicle_matching.catalog_merge import expand_catalog
from vehicle_matching.finance import Profile
from vehicle_matching.model import PairRanker
from vehicle_matching.service import CandidateService
from vehicle_matching.recommendation_policy import POLICY
from vehicle_matching.seating import apply_seating_registry
from vehicle_matching.specifications import apply_base_specifications, apply_specifications

logger = logging.getLogger(__name__)


class ProfileRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, strict=True)
    monthly_income: float = Field(ge=0, le=1e12)
    monthly_expenses: float = Field(ge=0, le=1e12)
    existing_monthly_payment: float = Field(ge=0, le=1e12)
    liquid_assets: float = Field(ge=0, le=1e12)
    down_payment: float = Field(default=0, ge=0, le=1e12, exclude=True, deprecated=True)
    emergency_reserve: float = Field(ge=0, le=1e12)
    monthly_savings: float = Field(ge=0, le=1e12)
    annual_distance: float = Field(ge=0, le=200000)
    months: int = Field(default=0, ge=0, le=72, strict=True, exclude=True, deprecated=True)
    annual_rate: float = Field(default=0, ge=0, le=1, exclude=True, deprecated=True)
    minimum_buffer: float = Field(default=0, ge=0, le=1e12)
    purpose: Literal['commute', 'leisure', 'family', 'business'] = 'commute'
    preferred_fuel: Literal['GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC'] | None = None
    charging_available: bool = Field(default=False, strict=True)
    cost_importance: int = Field(default=3, ge=1, le=5, strict=True)
    space_importance: int = Field(default=3, ge=1, le=5, strict=True)
    fuel_importance: int = Field(default=3, ge=1, le=5, strict=True)
    seating_importance: int = Field(default=3, ge=1, le=5, strict=True)
    purpose_importance: int = Field(default=1, ge=1, le=5, strict=True)
    purchase_price_ceiling: float = Field(default=0, ge=0, le=1e12)
    minimum_seats: int = Field(default=0, ge=0, le=9, strict=True)
    preferred_size: Literal['any', 'small', 'medium', 'large'] = 'any'
    preferred_body_type: Literal['any', 'SEDAN', 'SUV', 'HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP'] = 'any'
    body_importance: int = Field(default=3, ge=1, le=5, strict=True)
    financing_mode: Literal['fixed', 'automatic', 'recommendation'] = Field(default='recommendation', exclude=True, deprecated=True)


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    profile: ProfileRequest
    k: int = Field(default=3, ge=1, le=20, strict=True)


def load_service(directory, *, apply_specification_updates=True):
    path = Path(directory)
    meta = json.loads((path / 'metadata.json').read_text(encoding='utf-8'))
    if catalog_fingerprint(path / 'catalog.json') != meta['training']['catalog_sha256']:
        raise ValueError('Catalog checksum mismatch; explicitly train or version the new catalog')
    override = os.environ.get('ML_CANDIDATE_CATALOG')
    if override:
        from vehicle_matching.catalog import load_csv
        vehicles = load_csv(Path(override))[0] if Path(override).suffix.lower() == '.csv' else read_catalog(override)
    else:
        vehicles = read_catalog(path / 'catalog.json')
        vehicles, _ = expand_catalog(vehicles)
        vehicles = apply_base_specifications(vehicles)
        vehicles = apply_seating_registry(vehicles)
        if apply_specification_updates:
            vehicles = apply_specifications(vehicles)
    ranker = PairRanker.load(path)
    ranker.assumptions = replace(ranker.assumptions, acquisition_ratio=0, stress_rate_addition=0,
                                 stress_running_multiplier=1, version='cost-utility-v2.3-base-cost-only')
    from vehicle_matching.body_types import apply_body_types
    current = CandidateService(ranker, apply_body_types(vehicles, strict=False))
    current.model_bundle = path.name
    return current


def create_app(service=None):
    @asynccontextmanager
    async def lifespan(application):
        application.state.candidates = service or load_service(os.environ.get('ML_CANDIDATE_RUN', str(ROOT / 'ml/outputs/models/candidate-preferences/20261026-body-v1')))
        from vehicle_matching.managed_catalog import ManagedCatalog
        url=os.environ.get('ML_MANAGED_CATALOG_URL','http://127.0.0.1:8080/api/v1/vehicles/recommendation-catalog')
        application.state.managed_catalog = ManagedCatalog(url) if service is None and url else None
        yield

    application = FastAPI(title='Experimental user–vehicle ranking', lifespan=lifespan)

    def current_service(request):
        current=request.app.state.candidates
        provider=request.app.state.managed_catalog
        if provider is None:return current
        updated=CandidateService(current.ranker,provider.read())
        updated.model_bundle=current.model_bundle
        return updated

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error):
        errors = [{'field': '.'.join(map(str, item['loc'][1:])), 'message': item['msg']} for item in error.errors()]
        return problem(request, 400, '입력 오류', '필수 금액과 입력 범위를 확인해 주세요.', errors)

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, error):
        return problem(request, error.status_code, '요청 오류', '경로와 메서드를 확인해 주세요.')

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, error):
        logger.exception('Candidate inference failed')
        return problem(request, 500, '추천 처리 실패', '추천을 처리하지 못했습니다.')

    @application.get('/api/v2/recommendation-options')
    def options(request: Request):
        current = current_service(request)
        return {'success': True, 'data': {'modelVersion': 'candidate-v2', 'catalogCount': len(current.vehicles),
                'modelBundle': getattr(current, 'model_bundle', None),
                'scorePolicy': POLICY,
                'catalogSource': 'managed-database' if request.app.state.managed_catalog is not None else 'model-snapshot',
                'featureCount': len(current.ranker.mean) if hasattr(current.ranker, 'mean') else None,
                'rankerSchema': getattr(current.ranker, 'schema', 'candidate-v2'),
                'modelNames': len({(v.brand, v.model) for v in current.vehicles}),
                'verifiedLengthCount': sum(v.length_mm is not None for v in current.vehicles),
                'verifiedSeatsCount': sum(v.seats is not None and v.seats_status != 'user-provided' for v in current.vehicles),
                'registeredSeatingCount': sum(v.seats is not None or bool(v.seat_options) for v in current.vehicles),
                'seatingInputConflictCount': sum(v.seats_status == 'official-reference-conflict' for v in current.vehicles),
                'seatingOptionsCount': sum(bool(v.seat_options) for v in current.vehicles),
                'requiredFields': [name for name, field in ProfileRequest.model_fields.items() if field.is_required()],
                'assumptions': current.ranker.assumptions.to_dict()}}

    @application.post('/api/v2/recommendations')
    def recommendations(payload: RecommendationRequest, request: Request):
        try:
            profile = Profile(**payload.profile.model_dump(), down_payment=0, months=0, annual_rate=0, financing_mode='recommendation')
            return {'success': True, 'data': current_service(request).recommend(profile, payload.k)}
        except ValueError as error:
            return problem(request, 400, '입력 오류', str(error))

    return application


app = create_app()
