---
name: vehicle-dummy-data
description: 차량 보유자 더미 데이터의 시드·생성 파일, 프로필 조인, 금액 항등식, 컬럼 추가 방법을 적용한다. 더미 데이터를 생성·확장·검토할 때 사용한다.
---

# 차량 보유자 더미 데이터

생성 방법과 명령은 [data-generator/README.md](../../../data-generator/README.md) 를 기준으로 한다. 컬럼 정의의 기준은 [datagen/schema.py](../../../data-generator/datagen/schema.py) 이고, 이 스킬에 컬럼 목록을 복제하지 않는다.

## 파일

시드와 생성 결과는 파일 이름이 같고 폴더만 다르다.

- `owners.csv`: 보유자 재무 프로필
- `purchases.csv`: 트림과 구매 자금
- `owner-summary.csv`: 차량 라벨별 집계

| 구분 | 경로 | Git |
| --- | --- | --- |
| 시드 | `data/seed/domestic-car`, `data/seed/imported-car` | 포함 |
| 생성 결과 | `data/generated/` | 제외 |

`data/generated/` 에는 예전 9만 건 생성분도 들어 있다. 생성 명령은 이 경로를 덮어쓴다.

## 지켜야 할 관계

- 보유자와 구매는 `프로필_식별자` 로 1:1이다. 두 파일을 따로 샘플링하지 않는다.
- 보유자 대출잔액 = 차량 할부원금 + 기존 대출 잔액(보정 후)
- 보유자 월상환 = 차량 월상환 + 기존 월상환(보정 후)
- 총자산, 순자산, 소비 합계, 월잔여액, 옵션포함가, 총구매비용, 본인·가족·할부 재원은 구성 항목의 합과 같다.
- 구매직후 현금 = 현금성 자산, 구매직전 현금 = 구매직후 현금 + 본인자금
- 요약은 생성된 보유자 행을 집계한다. 요약 수치를 따로 난수 추출하지 않는다.
- 생성 식별자는 시드 `P` 식별자와 겹치지 않게 `GD` / `GI`, 차량 사양은 `GDC` / `GIC` 를 쓴다.

난수는 나이, 소득, 자산·소비 비율, 라벨, 트림 선택 같은 드라이버에만 둔다. 파생 컬럼은 공식으로 채운다.

## 컬럼 추가

1. `schema.py` 의 해당 스키마에 `Field` 를 추가한다. `driver` 는 샘플링 값, `derived` 는 계산 값이다.
2. `driver` 는 `seed.py` 에서 시드를 읽고 `generate.py` 의 `_build_pair` 에서 샘플링한다.
3. `derived` 는 `formulas.py` 또는 `_build_pair` 에서 계산한다.
4. 금액이 바뀌면 `tests/test_generate.py` 의 항등식 확인에 반영한다.
