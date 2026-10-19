from collections.abc import Mapping
from pathlib import Path

import numpy as np

from recommender.artifact import load_bundle
from recommender.dataset import profile_sample


def recommend(run_dir: Path, profile: Mapping[str, object], k: int = 3) -> list[dict[str, object]]:
    if k < 1:
        raise ValueError("k는 1 이상이어야 합니다")
    preprocessor, ranker = load_bundle(run_dir)
    catalog = preprocessor.labels
    if catalog is None:
        raise ValueError("저장된 라벨이 없습니다")
    prepared = preprocessor.transform([profile_sample(profile)], include_labels=False)
    probabilities = ranker.predict_proba(prepared)[0]
    width = min(k, probabilities.shape[0])
    order = np.argsort(-probabilities, kind="stable")[:width]
    return [
        {
            "라벨코드": catalog[int(index)].code,
            "모델": catalog[int(index)].model_name,
            "차체": catalog[int(index)].body,
            "차급": catalog[int(index)].grade,
            "확률": float(probabilities[index]),
        }
        for index in order
    ]
