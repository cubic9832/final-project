import json
from pathlib import Path

from legacy.recommender.models.mlp import MlpRanker
from legacy.recommender.preprocessing import PREPROCESSOR_FILE, Preprocessor
from legacy.recommender.ranking import Ranker

REPORT_FILE = "report.json"


def save_run(
    directory: Path,
    preprocessor: Preprocessor,
    ranker: Ranker,
    report: dict[str, object],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    preprocessor.save(directory / PREPROCESSOR_FILE)
    ranker.save(directory)
    (directory / REPORT_FILE).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_bundle(directory: Path) -> tuple[Preprocessor, MlpRanker]:
    preprocessor = Preprocessor.load(directory / PREPROCESSOR_FILE)
    ranker = MlpRanker.load(directory)
    if ranker.category_sizes != preprocessor.category_sizes:
        raise ValueError("모델과 전처리의 범주 크기가 다릅니다")
    if ranker.class_count != preprocessor.class_count:
        raise ValueError("모델과 전처리의 라벨 수가 다릅니다")
    return preprocessor, ranker


def read_report(directory: Path) -> dict[str, object]:
    return json.loads((directory / REPORT_FILE).read_text(encoding="utf-8"))
