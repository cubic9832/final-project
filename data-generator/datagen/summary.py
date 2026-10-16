import csv
from collections import Counter
from dataclasses import dataclass, field

from datagen.formulas import median, nearest_rank
from datagen.schema import SUMMARY_SCHEMA, column_names


@dataclass
class LabelSummary:
    model: str
    body: str
    grade: str
    count: int = 0
    age_sum: int = 0
    cash_sum: int = 0
    spend_sum: int = 0
    loan_sum: int = 0
    incomes: list[int] = field(default_factory=list)
    age_bands: Counter = field(default_factory=Counter)
    purposes: Counter = field(default_factory=Counter)

    def add(self, owner: dict[str, str]) -> None:
        self.count += 1
        self.age_sum += int(owner["나이_세"])
        self.cash_sum += int(owner["개인_현금성자산_원"])
        self.spend_sum += int(owner["개인_평균월소비합계_원"])
        self.loan_sum += int(owner["개인_평균월대출상환액_원"])
        self.incomes.append(int(owner["개인_연간세전소득_원"]))
        self.age_bands[owner["연령대"]] += 1
        self.purposes[owner["차량_이용목적"]] += 1


class SummaryAccumulator:
    def __init__(self) -> None:
        self.groups: dict[str, LabelSummary] = {}

    def add(self, owner: dict[str, str]) -> None:
        label = owner["보유차량_라벨코드"]
        group = self.groups.get(label)
        if group is None:
            group = LabelSummary(
                model=owner["보유차량_모델"],
                body=owner["보유차량_차체"],
                grade=owner["보유차량_차급"],
            )
            self.groups[label] = group
        group.add(owner)


def write_summary(path, accumulator: SummaryAccumulator) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=column_names(SUMMARY_SCHEMA),
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        for label in sorted(accumulator.groups):
            group = accumulator.groups[label]
            writer.writerow(
                {
                    "차량_라벨코드": label,
                    "모델": group.model,
                    "차체": group.body,
                    "차급": group.grade,
                    "보유자수": str(group.count),
                    "평균나이_세": str(_rounded_mean(group.age_sum, group.count)),
                    "연간세전소득_중앙값_원": str(median(group.incomes)),
                    "연간세전소득_10백분위_원": str(nearest_rank(group.incomes, 10)),
                    "연간세전소득_90백분위_원": str(nearest_rank(group.incomes, 90)),
                    "평균현금성자산_원": str(_rounded_mean(group.cash_sum, group.count)),
                    "평균월소비_원": str(_rounded_mean(group.spend_sum, group.count)),
                    "평균월대출상환액_원": str(_rounded_mean(group.loan_sum, group.count)),
                    "최빈연령대": _most_common(group.age_bands),
                    "최빈이용목적": _most_common(group.purposes),
                }
            )


def _rounded_mean(total: int, count: int) -> int:
    return int(round(total / count))


def _most_common(counter: Counter) -> str:
    top = max(counter.values())
    return sorted(key for key, count in counter.items() if count == top)[0]
