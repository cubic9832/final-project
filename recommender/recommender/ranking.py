from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import numpy as np

from recommender.preprocessing import PreparedSplit


class Ranker(Protocol):
    """교체하는 모델이 학습 루프에 맞추는 계약이다."""

    def fit(self, train: PreparedSplit, valid: PreparedSplit) -> None: ...

    def predict_proba(self, data: PreparedSplit) -> np.ndarray: ...

    def save(self, directory: Path) -> None: ...

    def describe(self) -> dict[str, object]: ...

    def learning_curve(self) -> tuple[int, list[dict[str, float | int]]]: ...


def select_best(scored: Sequence[tuple[Ranker, float]]) -> tuple[Ranker, float]:
    """검증 top-3이 가장 높은 모델을 고른다. 같으면 앞에 있는 모델을 유지한다."""
    if not scored:
        raise ValueError("비교할 모델이 없습니다")
    best_ranker, best_score = scored[0]
    for ranker, score in scored[1:]:
        if score > best_score:
            best_ranker = ranker
            best_score = score
    return best_ranker, best_score
