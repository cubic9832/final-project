"""학습 산출물을 서버 시작 시 읽고 재사용하는 추론 서비스."""
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from recommender.artifact import load_bundle
from recommender.dataset import CATEGORICAL_FEATURES, SEGMENTS, profile_sample, repo_root
from recommender.models.mlp import MlpRanker
from recommender.preprocessing import Preprocessor
from recommender.predict import recommend_loaded

logger = logging.getLogger(__name__)
SEGMENT_LABELS = {"domestic-car": "국내차", "imported-car": "수입차"}


@dataclass
class ModelBundle:
    directory: Path
    preprocessor: Preprocessor
    ranker: MlpRanker


class ModelRegistry:
    def __init__(self, bundles: dict[str, ModelBundle]):
        self.bundles = bundles

    @classmethod
    def load(cls) -> "ModelRegistry":
        bundles = {}
        for segment in SEGMENTS:
            variable = "ML_DOMESTIC_RUN" if segment == "domestic-car" else "ML_IMPORTED_RUN"
            configured = os.environ.get(variable)
            folder = repo_root() / "ml/outputs/models" / segment
            candidates = [p for p in folder.iterdir() if p.is_dir()] if folder.exists() else []
            # 실제 학습 CLI의 시각별 폴더를 통합 검증 폴더보다 우선한다.
            dated = [p for p in candidates if len(p.name) == 15 and p.name[8] == "T"
                     and p.name.replace("T", "").isdigit()]
            candidates = sorted(dated or candidates, key=lambda p: p.name, reverse=True)
            directory = Path(configured).resolve() if configured else (candidates[0] if candidates else None)
            if directory is None:
                continue
            try:
                preprocessor, ranker = load_bundle(directory)
                bundles[segment] = ModelBundle(directory, preprocessor, ranker)
            except (OSError, ValueError, RuntimeError, KeyError):
                logger.exception("추천 모델 로딩 실패: %s", segment)
        return cls(bundles)

    def options(self) -> list[dict]:
        options = []
        for segment in SEGMENTS:
            bundle = self.bundles.get(segment)
            categories = {}
            if bundle:
                categories = dict(zip(CATEGORICAL_FEATURES, bundle.preprocessor.categories))
            options.append({"code": segment, "label": SEGMENT_LABELS[segment],
                            "available": bundle is not None, "categories": categories})
        return options

    def recommend(self, segment: str, profile: dict, k: int) -> dict:
        bundle = self.bundles.get(segment)
        if bundle is None:
            raise LookupError("선택한 차량 구분의 추천 모델을 사용할 수 없습니다.")
        sample = profile_sample(profile)
        for index, name in enumerate(CATEGORICAL_FEATURES):
            if sample.categorical[index] not in bundle.preprocessor.categories[index]:
                raise ValueError(f"{name}: 제공된 선택지에서 선택해 주세요.")
        recommendations = recommend_loaded(bundle.preprocessor, bundle.ranker, profile, k)
        return {
            "segment": segment,
            "modelVersion": bundle.directory.name,
            "recommendations": [{"labelCode": item["라벨코드"], "model": item["모델"],
                                 "body": item["차체"], "grade": item["차급"],
                                 "probability": item["확률"]} for item in recommendations],
        }
