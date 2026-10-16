import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from recommender.dataset import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    Sample,
)

PREPROCESSOR_FILE = "preprocessor.json"


@dataclass(frozen=True)
class Label:
    code: str
    model_name: str
    body: str
    grade: str


@dataclass(frozen=True)
class PreparedSplit:
    numeric: np.ndarray
    categorical: np.ndarray
    category_sizes: tuple[int, ...]
    class_count: int
    labels: np.ndarray | None


class Preprocessor:
    """학습 분할로만 맞춘 수치 표준화와 범주 코드. 학습과 추론이 같은 transform을 쓴다."""

    def __init__(self) -> None:
        self.means: np.ndarray | None = None
        self.scales: np.ndarray | None = None
        self.categories: tuple[tuple[str, ...], ...] | None = None
        self.labels: tuple[Label, ...] | None = None

    @property
    def category_sizes(self) -> tuple[int, ...]:
        categories = self._fitted_categories()
        return tuple(len(vocab) + 1 for vocab in categories)

    @property
    def class_count(self) -> int:
        return len(self._fitted_labels())

    def fit(self, samples: Sequence[Sample]) -> None:
        if not samples:
            raise ValueError("학습 분할이 비어 있습니다")
        numeric = _numeric_matrix(samples)
        logged = np.log1p(numeric)
        means = logged.mean(axis=0)
        scales = logged.std(axis=0)
        scales[scales < 1e-8] = 1.0
        self.means = means
        self.scales = scales
        self.categories = tuple(
            tuple(sorted({sample.categorical[index] for sample in samples}))
            for index in range(len(CATEGORICAL_FEATURES))
        )
        self.labels = _label_catalog(samples)

    def transform(self, samples: Sequence[Sample], *, include_labels: bool = True) -> PreparedSplit:
        means, scales = self._fitted_numeric()
        categories = self._fitted_categories()
        labels = self._fitted_labels()
        if not samples:
            raise ValueError("변환할 행이 없습니다")
        logged = np.log1p(_numeric_matrix(samples))
        numeric = ((logged - means) / scales).astype(np.float32)
        categorical = np.column_stack(
            [
                [_category_index(categories[index], sample.categorical[index]) for sample in samples]
                for index in range(len(CATEGORICAL_FEATURES))
            ]
        ).astype(np.int64)
        label_index = None
        if include_labels:
            lookup = {label.code: index for index, label in enumerate(labels)}
            encoded = []
            for sample in samples:
                if sample.label_code not in lookup:
                    raise ValueError(f"학습에 없는 라벨입니다: {sample.label_code}")
                encoded.append(lookup[sample.label_code])
            label_index = np.asarray(encoded, dtype=np.int64)
        return PreparedSplit(
            numeric=numeric,
            categorical=categorical,
            category_sizes=self.category_sizes,
            class_count=self.class_count,
            labels=label_index,
        )

    def save(self, path: Path) -> None:
        means, scales = self._fitted_numeric()
        payload = {
            "numeric_features": list(NUMERIC_FEATURES),
            "categorical_features": list(CATEGORICAL_FEATURES),
            "means": means.tolist(),
            "scales": scales.tolist(),
            "categories": [list(vocab) for vocab in self._fitted_categories()],
            "labels": [
                {
                    "라벨코드": label.code,
                    "모델": label.model_name,
                    "차체": label.body,
                    "차급": label.grade,
                }
                for label in self._fitted_labels()
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Preprocessor":
        payload = json.loads(_read_text(path))
        if payload["numeric_features"] != list(NUMERIC_FEATURES):
            raise ValueError("저장된 수치 특징이 현재 코드와 다릅니다")
        if payload["categorical_features"] != list(CATEGORICAL_FEATURES):
            raise ValueError("저장된 범주 특징이 현재 코드와 다릅니다")
        preprocessor = cls()
        preprocessor.means = np.asarray(payload["means"], dtype=np.float64)
        preprocessor.scales = np.asarray(payload["scales"], dtype=np.float64)
        preprocessor.categories = tuple(tuple(vocab) for vocab in payload["categories"])
        preprocessor.labels = tuple(
            Label(
                code=item["라벨코드"],
                model_name=item["모델"],
                body=item["차체"],
                grade=item["차급"],
            )
            for item in payload["labels"]
        )
        if preprocessor.means.shape != (len(NUMERIC_FEATURES),):
            raise ValueError("저장된 수치 표준화가 특징 수와 다릅니다")
        if preprocessor.scales.shape != (len(NUMERIC_FEATURES),):
            raise ValueError("저장된 수치 표준화가 특징 수와 다릅니다")
        if len(preprocessor.categories) != len(CATEGORICAL_FEATURES):
            raise ValueError("저장된 범주 코드가 특징 수와 다릅니다")
        if not preprocessor.labels:
            raise ValueError("저장된 라벨이 없습니다")
        return preprocessor

    def _fitted_numeric(self) -> tuple[np.ndarray, np.ndarray]:
        if self.means is None or self.scales is None:
            raise ValueError("전처리가 학습 분할에 맞춰지기 전입니다")
        return self.means, self.scales

    def _fitted_categories(self) -> tuple[tuple[str, ...], ...]:
        if self.categories is None:
            raise ValueError("전처리가 학습 분할에 맞춰지기 전입니다")
        return self.categories

    def _fitted_labels(self) -> tuple[Label, ...]:
        if self.labels is None:
            raise ValueError("전처리가 학습 분할에 맞춰지기 전입니다")
        return self.labels


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"파일이 없습니다: {path.name}")
    return path.read_text(encoding="utf-8")


def _numeric_matrix(samples: Sequence[Sample]) -> np.ndarray:
    return np.asarray([sample.numeric for sample in samples], dtype=np.float64)


def _label_catalog(samples: Sequence[Sample]) -> tuple[Label, ...]:
    meta: dict[str, Label] = {}
    for sample in samples:
        label = Label(sample.label_code, sample.model_name, sample.body, sample.grade)
        previous = meta.get(sample.label_code)
        if previous is not None and previous != label:
            raise ValueError(f"라벨 {sample.label_code}의 차량 정보가 서로 다릅니다")
        meta[sample.label_code] = label
    if not meta:
        raise ValueError("학습 라벨이 없습니다")
    return tuple(meta[code] for code in sorted(meta))


def _category_index(vocab: tuple[str, ...], value: str) -> int:
    try:
        return vocab.index(value)
    except ValueError:
        return len(vocab)
