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
from vehicle_matching.finance import Profile
from vehicle_matching.model import PairRanker
from vehicle_matching.service import CandidateService

logger = logging.getLogger(__name__)


class ProfileRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, strict=True)
    monthly_income: float = Field(ge=0, le=1e12)
    monthly_expenses: float = Field(ge=0, le=1e12)
    existing_monthly_payment: float = Field(ge=0, le=1e12)
    liquid_assets: float = Field(ge=0, le=1e12)
    down_payment: float = Field(ge=0, le=1e12)
    emergency_reserve: float = Field(ge=0, le=1e12)
    monthly_savings: float = Field(ge=0, le=1e12)
    annual_distance: float = Field(ge=0, le=200000)
    months: int = Field(ge=0, le=72, strict=True)
    annual_rate: float = Field(default=0.06, ge=0, le=1)
    minimum_buffer: float = Field(default=0, ge=0, le=1e12)
    purpose: Literal['commute', 'leisure', 'family', 'business'] = 'commute'
    preferred_fuel: Literal['GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC'] | None = None
    charging_available: bool = Field(default=False, strict=True)
    cost_importance: int = Field(default=3, ge=1, le=5, strict=True)
    space_importance: int = Field(default=3, ge=1, le=5, strict=True)
    minimum_seats: int = Field(default=0, ge=0, le=9, strict=True)
    preferred_size: Literal['any', 'small', 'medium', 'large'] = 'any'


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    profile: ProfileRequest
    k: int = Field(default=3, ge=1, le=20, strict=True)


def load_service(directory):
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
        evidence = json.loads((ROOT / 'data/vehicles/candidate-space-evidence.json').read_text(encoding='utf-8'))['vehicles']
        lookup = {(row['brand'], row['model']): row for row in evidence}
        vehicles = [replace(v, length_mm=lookup[(v.brand, v.model)]['length_mm'],
                            space_source_url=lookup[(v.brand, v.model)]['source_url'])
                    if (v.brand, v.model) in lookup else v for v in vehicles]
    return CandidateService(PairRanker.load(path), vehicles)


def create_app(service=None):
    @asynccontextmanager
    async def lifespan(application):
        application.state.candidates = service or load_service(os.environ.get('ML_CANDIDATE_RUN', str(ROOT / 'ml/experiments/candidate-v2')))
        yield

    application = FastAPI(title='Experimental user–vehicle ranking', lifespan=lifespan)

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
        current = request.app.state.candidates
        return {'success': True, 'data': {'modelVersion': 'candidate-v2', 'catalogCount': len(current.vehicles),
                'modelNames': len({(v.brand, v.model) for v in current.vehicles}),
                'verifiedLengthCount': sum(v.length_mm is not None for v in current.vehicles),
                'verifiedSeatsCount': sum(v.seats is not None for v in current.vehicles),
                'requiredFields': [name for name, field in ProfileRequest.model_fields.items() if field.is_required()],
                'assumptions': current.ranker.assumptions.to_dict()}}

    @application.post('/api/v2/recommendations')
    def recommendations(payload: RecommendationRequest, request: Request):
        try:
            profile = Profile(**payload.profile.model_dump())
            return {'success': True, 'data': request.app.state.candidates.recommend(profile, payload.k)}
        except ValueError as error:
            return problem(request, 400, '입력 오류', str(error))

    return application


app = create_app()
