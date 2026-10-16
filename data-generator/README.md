# 차량 보유자 더미 데이터 생성기

시드의 차량 라벨별 분포를 따라 보유자·구매 내역을 늘립니다. 나이, 소득, 자산 비율처럼 난수가 들어가는 값은 드라이버이고, 총자산·상환액·구매 재원처럼 합계로 정해지는 값은 그 드라이버로 계산합니다.

## 준비

Python 3.11 이상과 numpy가 필요합니다.

```bash
cd data-generator
python3 -m venv .venv
source .venv/bin/activate
pip install numpy
```

Windows에서는 `.venv\Scripts\activate` 로 가상환경을 켭니다.

## 생성

```bash
python -m datagen generate --segment domestic-car --rows 100000 --seed 42
python -m datagen generate --segment imported-car --rows 100000 --seed 42
```

- `--segment` 는 `domestic-car` 또는 `imported-car` 입니다. 컬럼은 같고, 시드의 차량과 보유자 분포만 다릅니다.
- `--rows` 는 1 이상의 생성 건수입니다.
- `--seed` 는 난수 시드입니다. 기본값은 42이고, 같은 시드는 같은 파일을 만듭니다.
- `--output` 은 세 파일이 들어갈 디렉터리입니다. 생략하면 `data/generated/domestic-car` 또는 `data/generated/imported-car` 입니다.

각 디렉터리에 다음 파일이 생깁니다.

- `owners.csv` — 보유자 재무 프로필
- `purchases.csv` — 같은 사람의 트림·구매 자금. `프로필_식별자`가 보유자와 1:1입니다.
- `owner-summary.csv` — 차량 라벨별 집계. 따로 난수를 넣지 않고 보유자 행으로 계산합니다.

식별자는 시드의 `P000001`과 겹치지 않습니다. 국내차 프로필은 `GD0000001`, 수입차 프로필은 `GI0000001`, 차량 사양은 `GDC0000001`, `GIC0000001` 형식입니다.

## 시드와 생성 결과

| 역할 | 경로 | Git |
| --- | --- | --- |
| 국내차 시드 1만 건과 요약 | `data/seed/domestic-car/` | 포함 |
| 수입차 시드 6천 건과 요약 | `data/seed/imported-car/` | 포함 |
| 생성 결과 | `data/generated/` | 제외 |

시드와 생성 결과의 파일 이름은 같습니다. 폴더만 다릅니다.

지금 `data/generated/domestic-car` 와 `data/generated/imported-car` 에 있는 파일은 예전 9만 건 생성분입니다. 위 명령을 실행하면 그 파일을 덮어씁니다. 루트 [.gitignore](../.gitignore) 의 `data/generated/` 가 이 결과와 이후 생성분을 함께 제외합니다.

이전 파일 이름과의 대응은 다음과 같습니다.

- `차량보유자_재무특성_보정학습데이터.csv` → `data/seed/domestic-car/owners.csv`
- `보유차량_트림옵션_구매자금내역.csv` → `data/seed/domestic-car/purchases.csv`
- `차량별_보유자특성_보정요약.csv` → `data/seed/domestic-car/owner-summary.csv`
- `수입차_보유자_재무특성_학습데이터.csv` → `data/seed/imported-car/owners.csv`
- `수입차_트림옵션_구매자금내역.csv` → `data/seed/imported-car/purchases.csv`
- `수입차별_보유자특성_요약.csv` → `data/seed/imported-car/owner-summary.csv`
- `국내차_보유자_추가90000_학습데이터.csv` 외 국내 9만 건 → `data/generated/domestic-car/`
- `수입차_보유자_추가90000_학습데이터.csv` 외 수입 9만 건 → `data/generated/imported-car/`

## 계산으로 유지하는 관계

보유자:

- 총자산 = 현금성 + 기타금융 + 주거보증금 + 부동산
- 순자산 = 총자산 - 대출잔액
- 소비 합계 = 주거비 + 기타 생활소비
- 월잔여액 = 실수령 - 소비 합계 - 대출상환 - 저축
- 대출잔액 = 차량 할부원금 + 기존 대출 잔액(보정 후)
- 월대출상환 = 차량 월상환 + 기존 월상환(보정 후)
- 연령대는 나이에서, 경력 구분은 경력 연수에서 정합니다. 3년 이하는 사회초년생입니다.

구매:

- 옵션포함가 = 기본가격 + 옵션가격
- 등록비 = 옵션포함가의 7%
- 총구매비용 = 옵션포함가 + 등록비
- 본인자금 + 가족지원 + 할부원금 = 총구매비용
- 구매직후 현금 = 보유자 현금성 자산
- 구매직전 현금 = 구매직후 현금 + 본인자금
- 월이자 = 할부원금 × 연이율 / 12 의 반올림
- 월상환 = 원리금균등 상환액의 반올림, 월원금 = 월상환 - 월이자

같은 라벨의 시드 보유자를 고른 뒤 소득과 비율에 작은 배율을 곱합니다. 트림과 옵션은 그 라벨에서 실제로 나타난 사양 빈도를 따릅니다. 기본가격은 시드 값을 그대로 씁니다.

## 컬럼 추가

기준은 [datagen/schema.py](datagen/schema.py) 입니다.

1. `OWNER_SCHEMA`, `PURCHASE_SCHEMA`, `SUMMARY_SCHEMA` 중 해당 목록에 `Field("컬럼명", "driver")` 또는 `Field("컬럼명", "derived")` 를 추가합니다. 헤더 순서는 이 목록 순서입니다.
2. `driver` 이면 [datagen/seed.py](datagen/seed.py) 에서 시드 값을 읽고, [datagen/generate.py](datagen/generate.py) 의 `_build_pair` 에서 샘플링합니다.
3. `derived` 이면 `_build_pair` 또는 [datagen/formulas.py](datagen/formulas.py) 에서 다른 값으로 계산합니다. 파생 컬럼에 독립 난수를 넣지 않습니다.
4. 금액 컬럼이면 위의 합계가 계속 맞는지 [tests/test_generate.py](tests/test_generate.py) 에 확인을 추가합니다.

## 테스트

```bash
cd data-generator
source .venv/bin/activate
python -m unittest discover -s tests
```
