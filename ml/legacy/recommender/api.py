"""React에서 사용하는 추천 API. python -m uvicorn legacy.recommender.api:app으로 실행한다."""
from contextlib import asynccontextmanager
import logging
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException

from legacy.recommender.dataset import FEATURE_COLUMNS
from legacy.recommender.service import ModelRegistry

logger = logging.getLogger(__name__)


class RecommendationRequest(BaseModel):
    segment: Literal["all-cars"] = "all-cars"
    profile: dict[str, object]
    k: int = Field(default=3, ge=1, le=20)


def problem(request: Request, status: int, title: str, detail: str, errors=None):
    body = {"type": "about:blank", "title": title, "status": status,
            "detail": detail, "instance": request.url.path}
    if errors:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


def create_app(registry: ModelRegistry | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.models = registry if registry is not None else ModelRegistry.load()
        yield

    application = FastAPI(title="차량 추천 API", lifespan=lifespan)

    @application.exception_handler(RequestValidationError)
    async def invalid_body(request: Request, exception: RequestValidationError):
        return problem(request, 400, "입력 오류", "요청 형식과 필수 입력을 확인해 주세요.")

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exception: HTTPException):
        return problem(request, exception.status_code, "요청 오류", "요청한 리소스나 메서드를 확인해 주세요.")

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exception: Exception):
        logger.exception("추천 처리 실패", exc_info=exception)
        return problem(request, 500, "추천 처리 실패", "추천을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.")

    @application.get("/api/v1/recommendation-options")
    def options(request: Request):
        return {"success": True, "data": {"segments": request.app.state.models.options()}}

    @application.post("/api/v1/recommendations")
    def recommendations(payload: RecommendationRequest, request: Request):
        try:
            result = request.app.state.models.recommend(payload.segment, payload.profile, payload.k)
            return {"success": True, "data": result}
        except LookupError as error:
            return problem(request, 503, "추천 모델 준비 필요", str(error))
        except ValueError as error:
            field = next((name for name in FEATURE_COLUMNS if name in str(error)), None)
            errors = [{"field": field, "message": str(error)}] if field else None
            return problem(request, 400, "입력 오류", str(error), errors)

    return application


app = create_app()
