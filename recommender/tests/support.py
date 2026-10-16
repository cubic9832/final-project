import csv
from pathlib import Path

from recommender.dataset import (
    CATEGORICAL_FEATURES,
    LABEL_BODY,
    LABEL_CODE,
    LABEL_GRADE,
    LABEL_MODEL,
    LOAN_BEFORE,
    NUMERIC_FEATURES,
    PROFILE_ID,
    SPLIT_COLUMN,
    Sample,
)


def make_sample(
    *,
    split: str = "학습",
    label: str = "OWN001",
    model_name: str = "K5",
    body: str = "세단",
    grade: str = "중형",
    gender: str = "남성",
    job: str = "근로자",
    purpose: str = "출퇴근",
    income: float = 1000.0,
    age: float = 30.0,
) -> Sample:
    numeric = [1.0] * len(NUMERIC_FEATURES)
    numeric[NUMERIC_FEATURES.index("나이_세")] = age
    numeric[NUMERIC_FEATURES.index("개인_연간세전소득_원")] = income
    return Sample(
        numeric=tuple(numeric),
        categorical=(gender, job, purpose),
        split=split,
        label_code=label,
        model_name=model_name,
        body=body,
        grade=grade,
    )


def write_tables(directory: Path, specs: list[dict[str, object]]) -> None:
    owners: list[dict[str, str]] = []
    purchases: list[dict[str, str]] = []
    for index, spec in enumerate(specs, start=1):
        profile_id = str(spec.get("id", f"P{index:06d}"))
        owner = {column: "1" for column in NUMERIC_FEATURES if column != LOAN_BEFORE}
        owner.update(
            {
                PROFILE_ID: profile_id,
                "성별": str(spec.get("gender", "남성")),
                "직업_유형": str(spec.get("job", "근로자")),
                "차량_이용목적": str(spec.get("purpose", "출퇴근")),
                SPLIT_COLUMN: str(spec["split"]),
                LABEL_CODE: str(spec["label"]),
                "보유차량_브랜드": "기아",
                LABEL_MODEL: str(spec.get("model", "K5")),
                LABEL_BODY: str(spec.get("body", "세단")),
                LABEL_GRADE: str(spec.get("grade", "중형")),
                "개인_대출잔액_원": str(spec.get("leaked_loan", "999999")),
                "개인_월잔여액_원": "1",
                "기본가격_원": str(spec.get("price", "888")),
            }
        )
        if "income" in spec:
            owner["개인_연간세전소득_원"] = str(spec["income"])
        if "age" in spec:
            owner["나이_세"] = str(spec["age"])
        owners.append(owner)
        purchases.append(
            {
                PROFILE_ID: profile_id,
                LOAN_BEFORE: str(spec.get("loan", 0)),
                "기본가격_원": str(spec.get("price", "888")),
                "트림": "시그니처",
                "연료": "HYBRID",
            }
        )
    _write(directory / "owners.csv", owners)
    _write(directory / "purchases.csv", purchases)


def profile_from_sample(sample: Sample) -> dict[str, object]:
    profile: dict[str, object] = {}
    for name, value in zip(NUMERIC_FEATURES, sample.numeric):
        profile[name] = value
    for name, value in zip(CATEGORICAL_FEATURES, sample.categorical):
        profile[name] = value
    return profile


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
