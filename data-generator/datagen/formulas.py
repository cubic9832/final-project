import math

from datagen.schema import MONEY_UNIT, REGISTRATION_RATE, TAKEHOME_RATE


def round_to(value: float, unit: int = MONEY_UNIT) -> int:
    return int(round(value / unit) * unit)


def age_band(age: int) -> str:
    return f"{(age // 10) * 10}대"


def career_band(years: int) -> str:
    if years <= 3:
        return "사회초년생"
    return "경력자"


def monthly_takehome(annual_income: int) -> int:
    return round_to(annual_income * TAKEHOME_RATE / 12)


def registration_fee(option_included_price: int) -> int:
    return int(round(option_included_price * REGISTRATION_RATE))


def monthly_payment(principal: int, annual_rate: float, months: int) -> tuple[int, int, int]:
    """원리금균등 월상환과 첫 달 이자·원금 분할.

    반환은 (월원금상환, 월이자, 월상환)이다. 이자는 원금 * 연이율 / 12 를 반올림한 값이고,
    월상환은 원리금균등 상환액을 반올림한 값이다. 이자가 0이면 원금을 개월 수로 나눈다.
    """
    if principal <= 0 or months <= 0:
        return 0, 0, 0
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        payment = principal / months
    else:
        growth = (1 + monthly_rate) ** months
        payment = principal * monthly_rate * growth / (growth - 1)
    monthly = int(round(payment))
    interest = int(round(principal * annual_rate / 12))
    return monthly - interest, interest, monthly


def split_funding(total: int, loan_share: float, family_share: float) -> tuple[int, int, int]:
    """총구매비용을 본인자금, 가족지원, 할부원금으로 나눈다. 합은 total과 같다."""
    if total <= 0:
        return 0, 0, 0
    loan_share = min(max(loan_share, 0.0), 1.0)
    family_share = min(max(family_share, 0.0), 1.0)
    loan = int(round(total * loan_share))
    family = int(round(total * family_share))
    if loan > total:
        loan = total
    if loan + family > total:
        family = total - loan
    return total - loan - family, family, loan


def nearest_rank(values: list[int], percent: float) -> int:
    ordered = sorted(values)
    rank = math.ceil(percent / 100 * len(ordered))
    rank = min(max(rank, 1), len(ordered))
    return ordered[rank - 1]


def median(values: list[int]) -> int:
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2
    if count % 2 == 1:
        return ordered[middle]
    return int(round((ordered[middle - 1] + ordered[middle]) / 2))
