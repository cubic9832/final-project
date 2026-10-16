from datetime import datetime
from pathlib import Path

from recommender.artifact import save_run
from recommender.dataset import default_run_directory, load_dataset
from recommender.metrics import log_loss, top_k_hit_rate
from recommender.models.mlp import candidate_rankers
from recommender.preprocessing import Preprocessor
from recommender.ranking import Ranker, select_best


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
    validation_losses: list[float] = []
    for ranker in rankers:
        ranker.fit(train_split, valid_split)
        probabilities = ranker.predict_proba(valid_split)
        scored.append((ranker, top_k_hit_rate(probabilities, valid_split.labels, k=3)))
        validation_losses.append(log_loss(probabilities, valid_split.labels))
    best, best_score = select_best(scored)
    best_index = next(index for index, (ranker, _) in enumerate(scored) if ranker is best)

    evaluation_probabilities = best.predict_proba(evaluation_split)
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
            "validation": {"top3": best_score, "log_loss": validation_losses[best_index]},
            "evaluation": {
                "top3": top_k_hit_rate(evaluation_probabilities, evaluation_split.labels, k=3),
                "log_loss": log_loss(evaluation_probabilities, evaluation_split.labels),
            },
            "candidates": [
                {"model": ranker.describe(), "validation_top3": score}
                for ranker, score in scored
            ],
        },
    )
    return directory
