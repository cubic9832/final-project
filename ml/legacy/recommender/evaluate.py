from pathlib import Path

from legacy.recommender.artifact import load_bundle
from legacy.recommender.dataset import load_dataset
from legacy.recommender.metrics import log_loss, top_k_hit_rate


def evaluate_run(run_dir: Path, data_dir: Path) -> dict[str, float]:
    """저장된 묶음으로 평가 분할만 다시 잰다. 전처리는 학습 때 저장한 상태를 쓴다."""
    preprocessor, ranker = load_bundle(run_dir)
    dataset = load_dataset(data_dir)
    prepared = preprocessor.transform(dataset.evaluation)
    probabilities = ranker.predict_proba(prepared)
    labels = prepared.labels
    if labels is None:
        raise ValueError("평가 분할에 라벨이 없습니다")
    return {
        "top3": top_k_hit_rate(probabilities, labels, k=3),
        "log_loss": log_loss(probabilities, labels),
    }
