import csv
import math
import shutil
from pathlib import Path

import numpy as np

from datagen.formulas import (
    age_band,
    career_band,
    monthly_payment,
    monthly_takehome,
    registration_fee,
    round_to,
    split_funding,
)
from datagen.layout import PROFILE_PREFIX, SPEC_PREFIX
from datagen.schema import (
    INCOME_CHANGED,
    LABEL_BASIS,
    OWNER_SCHEMA,
    PURCHASE_SCHEMA,
    RULE_VERSION,
    SYNTHETIC,
    column_names,
)
from datagen.seed import SegmentModel, load_segment
from datagen.summary import SummaryAccumulator, write_summary

INCOME_FLOOR = 8_000_000
INCOME_CEILING = 800_000_000
AGE_FLOOR = 20
AGE_CEILING = 59
MILEAGE_FLOOR = 3_000
MILEAGE_CEILING = 40_000
JITTER_SIGMA = 0.08
OUTPUT_FILES = ("owners.csv", "purchases.csv", "owner-summary.csv")


def generate(*, segment: str, rows: int, seed: int, output_dir: Path) -> None:
    if rows < 1:
        raise ValueError("--rows 는 1 이상이어야 합니다")
    model = load_segment(segment)
    output_dir.mkdir(parents=True, exist_ok=True)
    partial = output_dir / ".partial"
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir()
    try:
        _write_rows(
            partial,
            model=model,
            rows=rows,
            seed=seed,
            segment=segment,
        )
        for name in OUTPUT_FILES:
            (partial / name).replace(output_dir / name)
    finally:
        if partial.exists():
            shutil.rmtree(partial)


def _write_rows(directory: Path, *, model: SegmentModel, rows: int, seed: int, segment: str) -> None:
    rng = np.random.default_rng(seed)
    summary = SummaryAccumulator()
    profile_prefix = PROFILE_PREFIX[segment]
    spec_prefix = SPEC_PREFIX[segment]
    with (
        (directory / "owners.csv").open("w", encoding="utf-8", newline="") as owner_file,
        (directory / "purchases.csv").open("w", encoding="utf-8", newline="") as purchase_file,
    ):
        owner_writer = _writer(owner_file, OWNER_SCHEMA)
        purchase_writer = _writer(purchase_file, PURCHASE_SCHEMA)
        owner_writer.writeheader()
        purchase_writer.writeheader()
        for index in range(1, rows + 1):
            owner, purchase = _build_pair(
                rng,
                model,
                profile_id=f"{profile_prefix}{index:07d}",
                spec_id=f"{spec_prefix}{index:07d}",
                seed=seed,
            )
            owner_writer.writerow(owner)
            purchase_writer.writerow(purchase)
            summary.add(owner)
    write_summary(directory / "owner-summary.csv", summary)


def _build_pair(
    rng: np.random.Generator,
    model: SegmentModel,
    *,
    profile_id: str,
    spec_id: str,
    seed: int,
) -> tuple[dict[str, str], dict[str, str]]:
    label = model.labels[int(rng.choice(len(model.labels), p=model.weights))]
    pool = model.donors_by_label[label]
    person = pool[int(rng.integers(0, len(pool)))]
    spec = pool[int(rng.integers(0, len(pool)))]

    age_offset = int(rng.integers(-2, 3))
    age = min(max(person.age + age_offset, AGE_FLOOR), AGE_CEILING)
    start_age = min(max(person.age - person.career_years, AGE_FLOOR), 30)
    career_years = max(0, age - start_age)

    income = round_to(person.annual_income * _factor(rng))
    income = min(max(income, INCOME_FLOOR), INCOME_CEILING)
    monthly_income = monthly_takehome(income)
    household_factor = _factor(rng)
    if person.household_size <= 1:
        household_income = monthly_income
    else:
        household_income = round_to(monthly_income * person.household_income_ratio * household_factor)
        household_income = max(household_income, monthly_income)

    cash = _money_from_ratio(income, person.cash_ratio, _factor(rng))
    financial = _money_from_ratio(income, person.financial_ratio, _factor(rng))
    deposit = _money_from_ratio(income, person.deposit_ratio, _factor(rng))
    realty = _money_from_ratio(income, person.realty_ratio, _factor(rng))
    housing = _money_from_ratio(monthly_income, person.housing_ratio, _factor(rng))
    other_spend = _money_from_ratio(monthly_income, person.other_spend_ratio, _factor(rng))
    saving = _money_from_ratio(monthly_income, person.saving_ratio, _factor(rng))
    mileage = int(round(person.mileage * _factor(rng)))
    mileage = min(max(mileage, MILEAGE_FLOOR), MILEAGE_CEILING)

    included = spec.base_price + spec.option_price
    fee = registration_fee(included)
    total = included + fee
    self_fund, family, principal = split_funding(
        total,
        person.loan_share * _factor(rng),
        person.family_share * _factor(rng),
    )
    principal_part, interest, vehicle_payment = monthly_payment(principal, spec.annual_rate, spec.term_months)

    existing_before = int(round(income * person.existing_before_ratio * _factor(rng)))
    existing_after = int(round(income * person.existing_after_ratio * _factor(rng)))
    if existing_after > existing_before:
        existing_before = existing_after
    existing_payment_before = _scaled_payment(existing_before, person.existing_pay_before_ratio)
    existing_payment_after = _scaled_payment(existing_after, person.existing_pay_after_ratio)
    prior_income = round_to(income * person.prior_income_ratio * _factor(rng))
    if prior_income <= 0:
        prior_income = income

    loan_balance = principal + existing_after
    loan_payment = vehicle_payment + existing_payment_after
    total_assets = cash + financial + deposit + realty
    spend = housing + other_spend
    split = _data_split(float(rng.random()))

    owner = _record(
        OWNER_SCHEMA,
        {
            "프로필_식별자": profile_id,
            "나이_세": age,
            "연령대": age_band(age),
            "성별": person.gender,
            "직업_유형": person.job,
            "경력_년": career_years,
            "경력_구분": career_band(career_years),
            "가구원수_명": person.household_size,
            "부양인원_명": person.dependents,
            "개인_연간세전소득_원": income,
            "개인_평균월실수령소득_원": monthly_income,
            "가구_평균월실수령소득_원": household_income,
            "개인_현금성자산_원": cash,
            "개인_기타금융자산_원": financial,
            "개인_주거보증금자산_원": deposit,
            "개인_부동산자산_원": realty,
            "개인_총자산_차량제외_원": total_assets,
            "개인_대출잔액_원": loan_balance,
            "개인_순자산_차량제외_원": total_assets - loan_balance,
            "개인_평균월주거비_원": housing,
            "개인_평균월기타생활소비_원": other_spend,
            "개인_평균월소비합계_원": spend,
            "개인_평균월대출상환액_원": loan_payment,
            "개인_평균월저축액_원": saving,
            "개인_월잔여액_원": monthly_income - spend - loan_payment - saving,
            "차량_이용목적": person.purpose,
            "연간_주행거리_km": mileage,
            "보유차량_라벨코드": person.label,
            "보유차량_브랜드": person.brand,
            "보유차량_모델": person.model,
            "보유차량_차체": person.body,
            "보유차량_차급": person.grade,
            "데이터_구분": split,
            "합성데이터_여부": SYNTHETIC,
            "라벨_근거": LABEL_BASIS,
            "생성규칙_버전": RULE_VERSION,
            "난수_시드": seed,
        },
    )
    purchase = _record(
        PURCHASE_SCHEMA,
        {
            "프로필_식별자": profile_id,
            "차량사양_식별자": spec_id,
            "기존_모델": spec.previous_model,
            "구매_모델": person.model,
            "연식_표기": spec.model_year,
            "파워트레인": spec.powertrain,
            "연료": spec.fuel,
            "트림": spec.trim,
            "기본가격_원": spec.base_price,
            "선택옵션": spec.option_name,
            "옵션가격_원": spec.option_price,
            "옵션포함가격_원": included,
            "등록비_가정_원": fee,
            "총구매비용_가정_원": total,
            "본인구매자금_원": self_fund,
            "가족지원금_가정_원": family,
            "차량할부원금_원": principal,
            "구매직전_현금_원": cash + self_fund,
            "구매직후_현금_원": cash,
            "구매당시_연간세전소득_가정_원": prior_income,
            "현재_개인연간세전소득_원": income,
            "소득변화_가정": INCOME_CHANGED,
            "할부기간_개월": spec.term_months,
            "차량할부_연금리_가정": spec.annual_rate_text,
            "차량_월원금상환액_원": principal_part,
            "차량_월이자_원": interest,
            "차량_월상환액_원": vehicle_payment,
            "기존대출잔액_보정후_원": existing_after,
            "기존월상환액_보정후_원": existing_payment_after,
            "기존월상환액_보정전_원": existing_payment_before,
            "기존대출잔액_보정전_원": existing_before,
            "옵션수집범위": spec.option_scope,
            "기본가격_출처_URL": spec.source_url,
            "기본가격_출처_페이지": spec.source_page,
        },
    )
    return owner, purchase


def _factor(rng: np.random.Generator) -> float:
    raw = math.exp(float(rng.normal(0.0, JITTER_SIGMA)))
    return min(max(raw, 0.5), 1.5)


def _money_from_ratio(base: int, ratio: float, factor: float) -> int:
    if ratio <= 0:
        return 0
    return max(0, round_to(base * ratio * factor))


def _scaled_payment(balance: int, pay_ratio: float) -> int:
    if balance <= 0 or pay_ratio <= 0:
        return 0
    return int(round(balance * pay_ratio))


def _data_split(roll: float) -> str:
    if roll < 0.70:
        return "학습"
    if roll < 0.85:
        return "평가"
    return "검증"


def _record(schema, values: dict) -> dict[str, str]:
    record = {}
    for field in schema:
        if field.name not in values:
            raise KeyError(field.name)
        value = values[field.name]
        record[field.name] = "" if value is None else str(value)
    return record


def _writer(file, schema) -> csv.DictWriter:
    return csv.DictWriter(
        file,
        fieldnames=column_names(schema),
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )
