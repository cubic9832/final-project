from datetime import datetime
from pathlib import Path

from legacy.recommender.artifact import save_run
from legacy.recommender.dataset import default_run_directory, load_dataset
from legacy.recommender.metrics import log_loss, top_k_hit_rate
from legacy.recommender.models.mlp import candidate_rankers
from legacy.recommender.preprocessing import PreparedSplit, Preprocessor
from legacy.recommender.ranking import Ranker, select_best


def train(
    data_dir: Path,
    *,
    segment: str,
    run_dir: Path | None = None,
    candidates: list[Ranker] | None = None,
) -> Path:
    dataset = load_dataset(data_dir)
    preprocessor = Preprocessor()
    preprocessor.fit(dataset.train)
    train_split = preprocessor.transform(dataset.train)
    valid_split = preprocessor.transform(dataset.valid)
    evaluation_split = preprocessor.transform(dataset.evaluation)

    rankers = candidates if candidates is not None else candidate_rankers()
    scored: list[tuple[Ranker, float]] = []
    for ranker in rankers:
        ranker.fit(train_split, valid_split)
        scored.append((ranker, _metrics(ranker, valid_split)["top3"]))
    best, _ = select_best(scored)
    selected_epoch, epochs = best.learning_curve()

    directory = run_dir or default_run_directory(segment, datetime.now().strftime("%Y%m%dT%H%M%S"))
    if directory.exists():
        raise ValueError(f"이미 있는 학습 결과입니다: {directory}")
    save_run(
        directory,
        preprocessor,
        best,
        {
            "segment": segment,
            "selected": best.describe(),
            "train": _metrics(best, train_split),
            "validation": _metrics(best, valid_split),
            "evaluation": _metrics(best, evaluation_split),
            "selected_epoch": selected_epoch,
            "epochs": epochs,
            "candidates": [
                {"model": ranker.describe(), "validation_top3": score}
                for ranker, score in scored
            ],
        },
    )
    return directory


def _metrics(ranker: Ranker, split: PreparedSplit) -> dict[str, float]:
    if split.labels is None:
        raise ValueError("지표를 계산할 라벨이 없습니다")
    probabilities = ranker.predict_proba(split)
    return {
        "top3": top_k_hit_rate(probabilities, split.labels, k=3),
        "log_loss": log_loss(probabilities, split.labels),
    }
