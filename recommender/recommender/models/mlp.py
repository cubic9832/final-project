import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from recommender.metrics import log_loss, top_k_hit_rate
from recommender.preprocessing import PreparedSplit

MODEL_FILE = "model.pt"
MODEL_CONFIG_FILE = "model.json"


@dataclass(frozen=True)
class MlpConfig:
    hidden: tuple[int, int] = (64, 32)
    dropout: float = 0.1
    lr: float = 1e-3
    epochs: int = 30
    batch_size: int = 256
    embedding_dim: int = 8
    seed: int = 42

    def __post_init__(self) -> None:
        if len(self.hidden) != 2 or any(size < 1 for size in self.hidden):
            raise ValueError("은닉층은 두 개의 양수 크기여야 합니다")
        if not 0 <= self.dropout < 1:
            raise ValueError("dropout은 0 이상 1 미만이어야 합니다")
        if self.lr <= 0 or self.epochs < 1 or self.batch_size < 1 or self.embedding_dim < 1:
            raise ValueError("학습 설정이 올바르지 않습니다")

    def to_dict(self) -> dict[str, object]:
        return {
            "hidden": list(self.hidden),
            "dropout": self.dropout,
            "lr": self.lr,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "embedding_dim": self.embedding_dim,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "MlpConfig":
        hidden = payload["hidden"]
        if not isinstance(hidden, list):
            raise ValueError("은닉층 설정이 올바르지 않습니다")
        return cls(
            hidden=(int(hidden[0]), int(hidden[1])),
            dropout=float(payload["dropout"]),
            lr=float(payload["lr"]),
            epochs=int(payload["epochs"]),
            batch_size=int(payload["batch_size"]),
            embedding_dim=int(payload["embedding_dim"]),
            seed=int(payload["seed"]),
        )


class MlpRanker:
    """범주 임베딩과 수치를 이어 붙인 다층 퍼셉트론."""

    def __init__(self, config: MlpConfig | None = None) -> None:
        self.config = config or MlpConfig()
        self._net: _MlpNet | None = None
        self._category_sizes: tuple[int, ...] | None = None
        self._class_count: int | None = None
        self.epoch_history: list[dict[str, float | int]] = []
        self.selected_epoch: int | None = None

    @property
    def category_sizes(self) -> tuple[int, ...]:
        if self._category_sizes is None:
            raise ValueError("학습되지 않은 모델입니다")
        return self._category_sizes

    @property
    def class_count(self) -> int:
        if self._class_count is None:
            raise ValueError("학습되지 않은 모델입니다")
        return self._class_count

    def fit(self, train: PreparedSplit, valid: PreparedSplit) -> None:
        _require_same_layout(train, valid)
        if train.labels is None or valid.labels is None:
            raise ValueError("학습에는 라벨이 필요합니다")
        torch.manual_seed(self.config.seed)
        net = _MlpNet(
            numeric_count=train.numeric.shape[1],
            category_sizes=train.category_sizes,
            class_count=train.class_count,
            hidden=self.config.hidden,
            dropout=self.config.dropout,
            embedding_dim=self.config.embedding_dim,
        )
        optimizer = torch.optim.Adam(net.parameters(), lr=self.config.lr)
        loss_fn = nn.CrossEntropyLoss()
        train_numeric = torch.from_numpy(train.numeric)
        train_categorical = torch.from_numpy(train.categorical)
        train_labels = torch.from_numpy(train.labels)
        generator = torch.Generator()
        generator.manual_seed(self.config.seed)

        best_state: dict[str, torch.Tensor] | None = None
        best_key: tuple[float, float] | None = None
        best_epoch = 0
        history: list[dict[str, float | int]] = []
        for epoch in range(1, self.config.epochs + 1):
            net.train()
            for numeric, categorical, labels in _batches(
                train_numeric,
                train_categorical,
                train_labels,
                self.config.batch_size,
                generator,
            ):
                optimizer.zero_grad()
                loss = loss_fn(net(numeric, categorical), labels)
                loss.backward()
                optimizer.step()
            train_probabilities = _probabilities(net, train)
            valid_probabilities = _probabilities(net, valid)
            train_top3 = top_k_hit_rate(train_probabilities, train.labels, k=3)
            train_loss = log_loss(train_probabilities, train.labels)
            valid_top3 = top_k_hit_rate(valid_probabilities, valid.labels, k=3)
            valid_loss = log_loss(valid_probabilities, valid.labels)
            history.append(
                {
                    "epoch": epoch,
                    "train_top3": train_top3,
                    "train_log_loss": train_loss,
                    "validation_top3": valid_top3,
                    "validation_log_loss": valid_loss,
                }
            )
            key = (valid_top3, -valid_loss)
            if best_key is None or key > best_key:
                best_key = key
                best_epoch = epoch
                best_state = {name: value.detach().cpu().clone() for name, value in net.state_dict().items()}
        if best_state is None:
            raise ValueError("학습 에포크가 없습니다")
        net.load_state_dict(best_state)
        net.eval()
        self._net = net
        self._category_sizes = train.category_sizes
        self._class_count = train.class_count
        self.epoch_history = history
        self.selected_epoch = best_epoch

    def predict_proba(self, data: PreparedSplit) -> np.ndarray:
        net = self._require_net()
        if data.category_sizes != self.category_sizes or data.class_count != self.class_count:
            raise ValueError("전처리 결과와 모델의 출력 크기가 다릅니다")
        return _probabilities(net, data)

    def save(self, directory: Path) -> None:
        net = self._require_net()
        directory.mkdir(parents=True, exist_ok=True)
        torch.save(net.state_dict(), directory / MODEL_FILE)
        payload = {
            "config": self.config.to_dict(),
            "numeric_count": net.numeric_count,
            "category_sizes": list(self.category_sizes),
            "class_count": self.class_count,
        }
        (directory / MODEL_CONFIG_FILE).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, directory: Path) -> "MlpRanker":
        config_path = directory / MODEL_CONFIG_FILE
        weights_path = directory / MODEL_FILE
        if not config_path.is_file():
            raise ValueError(f"파일이 없습니다: {MODEL_CONFIG_FILE}")
        if not weights_path.is_file():
            raise ValueError(f"파일이 없습니다: {MODEL_FILE}")
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        ranker = cls(MlpConfig.from_dict(payload["config"]))
        category_sizes = tuple(int(size) for size in payload["category_sizes"])
        net = _MlpNet(
            numeric_count=int(payload["numeric_count"]),
            category_sizes=category_sizes,
            class_count=int(payload["class_count"]),
            hidden=ranker.config.hidden,
            dropout=ranker.config.dropout,
            embedding_dim=ranker.config.embedding_dim,
        )
        state = torch.load(weights_path, map_location="cpu", weights_only=True)
        net.load_state_dict(state)
        net.eval()
        ranker._net = net
        ranker._category_sizes = category_sizes
        ranker._class_count = int(payload["class_count"])
        return ranker

    def describe(self) -> dict[str, object]:
        return self.config.to_dict()

    def learning_curve(self) -> tuple[int, list[dict[str, float | int]]]:
        if self.selected_epoch is None:
            raise ValueError("학습 곡선이 없습니다")
        return self.selected_epoch, self.epoch_history

    def _require_net(self) -> "_MlpNet":
        if self._net is None:
            raise ValueError("학습되지 않은 모델입니다")
        return self._net


def candidate_rankers() -> list[MlpRanker]:
    """검증 top-3으로 고를 MLP 설정이다. 탐색 범위는 이 모델 쪽에만 둔다."""
    return [
        MlpRanker(MlpConfig(hidden=(32, 16), dropout=0.0, lr=1e-3)),
        MlpRanker(MlpConfig(hidden=(64, 32), dropout=0.1, lr=1e-3)),
        MlpRanker(MlpConfig(hidden=(128, 64), dropout=0.2, lr=3e-4)),
    ]


class _MlpNet(nn.Module):
    def __init__(
        self,
        numeric_count: int,
        category_sizes: tuple[int, ...],
        class_count: int,
        hidden: tuple[int, int],
        dropout: float,
        embedding_dim: int,
    ) -> None:
        super().__init__()
        self.numeric_count = numeric_count
        self.embeddings = nn.ModuleList(nn.Embedding(size, embedding_dim) for size in category_sizes)
        width = numeric_count + embedding_dim * len(category_sizes)
        blocks: list[nn.Module] = []
        for size in hidden:
            blocks.append(nn.Linear(width, size))
            blocks.append(nn.ReLU())
            blocks.append(nn.Dropout(dropout))
            width = size
        self.hidden = nn.Sequential(*blocks)
        self.output = nn.Linear(width, class_count)

    def forward(self, numeric: torch.Tensor, categorical: torch.Tensor) -> torch.Tensor:
        embedded = [embedding(categorical[:, index]) for index, embedding in enumerate(self.embeddings)]
        features = torch.cat([numeric, *embedded], dim=1)
        return self.output(self.hidden(features))


def _require_same_layout(train: PreparedSplit, valid: PreparedSplit) -> None:
    if train.category_sizes != valid.category_sizes or train.class_count != valid.class_count:
        raise ValueError("학습과 검증의 전처리 크기가 다릅니다")
    if train.numeric.shape[1] == 0 or train.class_count < 1:
        raise ValueError("학습 특징 또는 라벨이 없습니다")


def _batches(
    numeric: torch.Tensor,
    categorical: torch.Tensor,
    labels: torch.Tensor,
    batch_size: int,
    generator: torch.Generator,
):
    order = torch.randperm(labels.shape[0], generator=generator)
    for start in range(0, labels.shape[0], batch_size):
        index = order[start : start + batch_size]
        yield numeric[index], categorical[index], labels[index]


def _probabilities(net: _MlpNet, data: PreparedSplit) -> np.ndarray:
    net.eval()
    with torch.no_grad():
        logits = net(torch.from_numpy(data.numeric), torch.from_numpy(data.categorical))
        return torch.softmax(logits, dim=1).numpy()
