import csv
from typing import NamedTuple

import numpy as np

from datagen.layout import SEGMENTS, seed_directory


class Donor(NamedTuple):
    age: int
    career_years: int
    gender: str
    job: str
    household_size: int
    dependents: int
    purpose: str
    annual_income: int
    cash_ratio: float
    financial_ratio: float
    deposit_ratio: float
    realty_ratio: float
    housing_ratio: float
    other_spend_ratio: float
    saving_ratio: float
    mileage: int
    household_income_ratio: float
    loan_share: float
    family_share: float
    annual_rate: float
    annual_rate_text: str
    term_months: int
    prior_income_ratio: float
    existing_before_ratio: float
    existing_after_ratio: float
    existing_pay_before_ratio: float
    existing_pay_after_ratio: float
    previous_model: str
    model_year: str
    powertrain: str
    fuel: str
    trim: str
    base_price: int
    option_name: str
    option_price: int
    option_scope: str
    source_url: str
    source_page: str
    label: str
    brand: str
    model: str
    body: str
    grade: str


class SegmentModel(NamedTuple):
    labels: tuple[str, ...]
    weights: np.ndarray
    donors_by_label: dict[str, list[Donor]]


def load_segment(segment: str) -> SegmentModel:
    if segment not in SEGMENTS:
        raise ValueError(f"알 수 없는 세그먼트입니다: {segment}")
    directory = seed_directory(segment)
    owners = _read_csv(directory / "owners.csv")
    purchases = _read_csv(directory / "purchases.csv")
    purchase_by_id = {row["프로필_식별자"]: row for row in purchases}
    if len(purchase_by_id) != len(purchases):
        raise ValueError("구매 내역의 프로필 식별자가 중복됩니다")
    if len(owners) != len(purchase_by_id):
        raise ValueError("보유자와 구매 내역의 건수가 다릅니다")

    donors_by_label: dict[str, list[Donor]] = {}
    for owner in owners:
        profile_id = owner["프로필_식별자"]
        purchase = purchase_by_id.get(profile_id)
        if purchase is None:
            raise ValueError(f"구매 내역이 없는 보유자입니다: {profile_id}")
        donor = _donor(owner, purchase)
        donors_by_label.setdefault(donor.label, []).append(donor)

    for label, donors in donors_by_label.items():
        head = donors[0]
        identity = (head.brand, head.model, head.body, head.grade)
        for donor in donors[1:]:
            if (donor.brand, donor.model, donor.body, donor.grade) != identity:
                raise ValueError(f"라벨 {label}의 차량 정보가 서로 다릅니다")

    labels = tuple(sorted(donors_by_label))
    counts = np.array([len(donors_by_label[label]) for label in labels], dtype=np.float64)
    weights = counts / counts.sum()
    return SegmentModel(labels=labels, weights=weights, donors_by_label=donors_by_label)


def _read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f"시드 파일이 없습니다: {path}")
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _donor(owner: dict[str, str], purchase: dict[str, str]) -> Donor:
    annual_income = _parse_int(owner["개인_연간세전소득_원"])
    monthly_income = _parse_int(owner["개인_평균월실수령소득_원"])
    total_price = _parse_int(purchase["총구매비용_가정_원"])
    existing_before = _parse_int(purchase["기존대출잔액_보정전_원"])
    existing_after = _parse_int(purchase["기존대출잔액_보정후_원"])
    return Donor(
        age=_parse_int(owner["나이_세"]),
        career_years=_parse_int(owner["경력_년"]),
        gender=owner["성별"],
        job=owner["직업_유형"],
        household_size=_parse_int(owner["가구원수_명"]),
        dependents=_parse_int(owner["부양인원_명"]),
        purpose=owner["차량_이용목적"],
        annual_income=annual_income,
        cash_ratio=_ratio(_parse_int(owner["개인_현금성자산_원"]), annual_income),
        financial_ratio=_ratio(_parse_int(owner["개인_기타금융자산_원"]), annual_income),
        deposit_ratio=_ratio(_parse_int(owner["개인_주거보증금자산_원"]), annual_income),
        realty_ratio=_ratio(_parse_int(owner["개인_부동산자산_원"]), annual_income),
        housing_ratio=_ratio(_parse_int(owner["개인_평균월주거비_원"]), monthly_income),
        other_spend_ratio=_ratio(_parse_int(owner["개인_평균월기타생활소비_원"]), monthly_income),
        saving_ratio=_ratio(_parse_int(owner["개인_평균월저축액_원"]), monthly_income),
        mileage=_parse_int(owner["연간_주행거리_km"]),
        household_income_ratio=_ratio(_parse_int(owner["가구_평균월실수령소득_원"]), monthly_income),
        loan_share=_ratio(_parse_int(purchase["차량할부원금_원"]), total_price),
        family_share=_ratio(_parse_int(purchase["가족지원금_가정_원"]), total_price),
        annual_rate=float(purchase["차량할부_연금리_가정"] or 0),
        annual_rate_text=purchase["차량할부_연금리_가정"],
        term_months=_parse_int(purchase["할부기간_개월"]),
        prior_income_ratio=_ratio(_parse_int(purchase["구매당시_연간세전소득_가정_원"]), annual_income),
        existing_before_ratio=_ratio(existing_before, annual_income),
        existing_after_ratio=_ratio(existing_after, annual_income),
        existing_pay_before_ratio=_ratio(_parse_int(purchase["기존월상환액_보정전_원"]), existing_before),
        existing_pay_after_ratio=_ratio(_parse_int(purchase["기존월상환액_보정후_원"]), existing_after),
        previous_model=purchase["기존_모델"],
        model_year=purchase["연식_표기"],
        powertrain=purchase["파워트레인"],
        fuel=purchase["연료"],
        trim=purchase["트림"],
        base_price=_parse_int(purchase["기본가격_원"]),
        option_name=purchase["선택옵션"],
        option_price=_parse_int(purchase["옵션가격_원"]),
        option_scope=purchase["옵션수집범위"],
        source_url=purchase["기본가격_출처_URL"],
        source_page=purchase["기본가격_출처_페이지"],
        label=owner["보유차량_라벨코드"],
        brand=owner["보유차량_브랜드"],
        model=owner["보유차량_모델"],
        body=owner["보유차량_차체"],
        grade=owner["보유차량_차급"],
    )


def _parse_int(value: str) -> int:
    text = value.strip()
    if text == "":
        return 0
    if "." in text:
        return int(float(text))
    return int(text)


def _ratio(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return part / whole
