import numpy as np


def top_k_hit_rate(probabilities: np.ndarray, labels: np.ndarray, k: int = 3) -> float:
    if labels.size == 0:
        raise ValueError("평가할 행이 없습니다")
    if k < 1:
        raise ValueError("k는 1 이상이어야 합니다")
    width = min(k, probabilities.shape[1])
    top = np.argsort(-probabilities, axis=1)[:, :width]
    hits = (top == labels.reshape(-1, 1)).any(axis=1)
    return float(hits.mean())


def log_loss(probabilities: np.ndarray, labels: np.ndarray) -> float:
    if labels.size == 0:
        raise ValueError("평가할 행이 없습니다")
    clipped = np.clip(probabilities, 1e-12, 1.0)
    chosen = clipped[np.arange(len(labels)), labels]
    return float(-np.log(chosen).mean())
