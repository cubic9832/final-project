import csv
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

SEGMENTS = ("domestic-car", "imported-car")
PROFILE_ID = "프로필_식별자"
SPLIT_COLUMN = "데이터_구분"
SPLIT_TRAIN = "학습"
SPLIT_VALID = "검증"
SPLIT_EVALUATION = "평가"
SPLITS = (SPLIT_TRAIN, SPLIT_VALID, SPLIT_EVALUATION)

# 구매 전에 알 수 있는 값만 특징으로 쓴다.
NUMERIC_FEATURES = (
    "나이_세",
    "경력_년",
    "가구원수_명",
    "부양인원_명",
    "개인_연간세전소득_원",
    "개인_현금성자산_원",
    "개인_기타금융자산_원",
    "개인_주거보증금자산_원",
    "개인_부동산자산_원",
    "개인_평균월주거비_원",
    "개인_평균월기타생활소비_원",
    "개인_평균월저축액_원",
    "연간_주행거리_km",
    "기존대출잔액_보정전_원",
)
CATEGORICAL_FEATURES = (
    "성별",
    "직업_유형",
    "차량_이용목적",
)
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

LABEL_CODE = "보유차량_라벨코드"
LABEL_MODEL = "보유차량_모델"
LABEL_BODY = "보유차량_차체"
LABEL_GRADE = "보유차량_차급"
LOAN_BEFORE = "기존대출잔액_보정전_원"

# 차가 정해진 뒤에만 알 수 있거나, 그 차의 할부가 섞인 컬럼이다.
LEAKED_COLUMNS = (
    LABEL_CODE,
    "보유차량_브랜드",
    LABEL_MODEL,
    LABEL_BODY,
    LABEL_GRADE,
    "개인_대출잔액_원",
    "개인_순자산_차량제외_원",
    "개인_평균월대출상환액_원",
    "개인_월잔여액_원",
    "기존_모델",
    "구매_모델",
    "기본가격_원",
    "트림",
    "연료",
    "파워트레인",
    "선택옵션",
    "옵션가격_원",
    "옵션포함가격_원",
    "총구매비용_가정_원",
    "차량할부원금_원",
    "차량_월상환액_원",
    "차량_월원금상환액_원",
    "차량_월이자_원",
    SPLIT_COLUMN,
    "합성데이터_여부",
    "라벨_근거",
    "생성규칙_버전",
    "난수_시드",
    "기본가격_출처_URL",
    "기본가격_출처_페이지",
)


@dataclass(frozen=True)
class Sample:
    numeric: tuple[float, ...]
    categorical: tuple[str, ...]
    split: str = ""
    label_code: str = ""
    model_name: str = ""
    body: str = ""
    grade: str = ""


@dataclass(frozen=True)
class Dataset:
    train: tuple[Sample, ...]
    valid: tuple[Sample, ...]
    evaluation: tuple[Sample, ...]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def seed_directory(segment: str) -> Path:
    _require_segment(segment)
    return repo_root() / "data" / "seed" / segment


def default_run_directory(segment: str, run_id: str) -> Path:
    _require_segment(segment)
    return repo_root() / "recommender" / "runs" / segment / run_id


def feature_columns() -> tuple[str, ...]:
    overlap = set(FEATURE_COLUMNS) & set(LEAKED_COLUMNS)
    if overlap:
        names = ", ".join(sorted(overlap))
        raise ValueError(f"누수 컬럼이 특징에 포함되어 있습니다: {names}")
    return FEATURE_COLUMNS


def load_dataset(data_dir: Path) -> Dataset:
    feature_columns()
    owners = _read_csv(data_dir / "owners.csv")
    purchases = _read_csv(data_dir / "purchases.csv")
    purchase_by_id = _index_purchases(purchases)
    if len(purchase_by_id) != len(owners):
        raise ValueError("보유자와 구매 내역의 건수가 다릅니다")

    seen: set[str] = set()
    grouped: dict[str, list[Sample]] = {split: [] for split in SPLITS}
    label_meta: dict[str, tuple[str, str, str]] = {}
    for owner in owners:
        profile_id = _require_text(owner, PROFILE_ID)
        if profile_id in seen:
            raise ValueError(f"보유자 식별자가 중복됩니다: {profile_id}")
        seen.add(profile_id)
        purchase = purchase_by_id.get(profile_id)
        if purchase is None:
            raise ValueError(f"구매 내역이 없는 보유자입니다: {profile_id}")
        sample = _sample_from_rows(owner, purchase)
        _remember_label(label_meta, sample)
        if sample.split not in grouped:
            raise ValueError(f"알 수 없는 데이터 구분입니다: {sample.split}")
        grouped[sample.split].append(sample)

    missing = [split for split in SPLITS if not grouped[split]]
    if missing:
        raise ValueError(f"비어 있는 데이터 구분이 있습니다: {', '.join(missing)}")
    return Dataset(
        train=tuple(grouped[SPLIT_TRAIN]),
        valid=tuple(grouped[SPLIT_VALID]),
        evaluation=tuple(grouped[SPLIT_EVALUATION]),
    )


def profile_sample(profile: Mapping[str, object]) -> Sample:
    """추론 입력이다. 정답과 구매 결과 컬럼이 있어도 특징으로 읽지 않는다."""
    return Sample(
        numeric=tuple(_parse_number(profile, name) for name in NUMERIC_FEATURES),
        categorical=tuple(_parse_category(profile, name) for name in CATEGORICAL_FEATURES),
    )


def _require_segment(segment: str) -> None:
    if segment not in SEGMENTS:
        raise ValueError(f"알 수 없는 세그먼트입니다: {segment}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"파일이 없습니다: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _index_purchases(purchases: Sequence[Mapping[str, str]]) -> dict[str, Mapping[str, str]]:
    indexed: dict[str, Mapping[str, str]] = {}
    for purchase in purchases:
        profile_id = _require_text(purchase, PROFILE_ID)
        if profile_id in indexed:
            raise ValueError(f"구매 내역의 프로필 식별자가 중복됩니다: {profile_id}")
        indexed[profile_id] = purchase
    return indexed


def _sample_from_rows(owner: Mapping[str, str], purchase: Mapping[str, str]) -> Sample:
    values = dict(owner)
    values[LOAN_BEFORE] = _require_text(purchase, LOAN_BEFORE)
    return Sample(
        numeric=tuple(_parse_number(values, name) for name in NUMERIC_FEATURES),
        categorical=tuple(_parse_category(values, name) for name in CATEGORICAL_FEATURES),
        split=_require_text(owner, SPLIT_COLUMN),
        label_code=_require_text(owner, LABEL_CODE),
        model_name=_require_text(owner, LABEL_MODEL),
        body=_require_text(owner, LABEL_BODY),
        grade=_require_text(owner, LABEL_GRADE),
    )


def _remember_label(known: dict[str, tuple[str, str, str]], sample: Sample) -> None:
    meta = (sample.model_name, sample.body, sample.grade)
    previous = known.get(sample.label_code)
    if previous is not None and previous != meta:
        raise ValueError(f"라벨 {sample.label_code}의 차량 정보가 서로 다릅니다")
    known[sample.label_code] = meta


def _require_text(row: Mapping[str, object], column: str) -> str:
    if column not in row:
        raise ValueError(f"{column} 컬럼이 없습니다")
    return _parse_category(row, column)


def _parse_number(row: Mapping[str, object], column: str) -> float:
    if column not in row:
        raise ValueError(f"{column} 컬럼이 없습니다")
    value = row[column]
    if isinstance(value, bool) or value is None or value == "":
        raise ValueError(f"{column} 값이 없습니다")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{column} 값이 숫자가 아닙니다") from error
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{column} 값은 0 이상이어야 합니다")
    return number


def _parse_category(row: Mapping[str, object], column: str) -> str:
    if column not in row:
        raise ValueError(f"{column} 컬럼이 없습니다")
    value = row[column]
    if value is None:
        raise ValueError(f"{column} 값이 없습니다")
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{column} 값이 없습니다")
    return text
