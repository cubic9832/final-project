# 차량별 학습 사례 보완본

`preference-quality-v1`의 기존 206,156행을 값·순서·분리 구분까지 그대로 유지하고 신규 학습 사례 273행을 추가했다. 총 206,429행이며 학습 138,300행, 검증 24,194행, 평가 43,935행이다. main과 원본 데이터는 수정하지 않는다.

| 차량 | 기존 학습 | 추가 | 보완 후 |
| --- | ---: | ---: | ---: |
| G90 | 25 | 75 | 100 |
| G90 Long Wheel Base | 2 | 98 | 100 |
| G90 Long Wheel Base Black | 0 | 100 | 100 |

현재 데이터에 등장하는 46개 차량 라벨 모두 학습에 최소 100행이 존재한다. 이는 데이터에 등장하지 않는 전체 카탈로그 차량까지 학습했다는 의미는 아니다. 100행은 초기 사례 확보 기준이며 분류 성능이나 균형 잡힌 학습을 보장하지 않는다. 희소 차량의 검증·평가 표본 수도 여전히 작으므로 차량별 정확도 해석에 주의해야 한다.

## 생성과 검증

- 기존 생성기의 재무·선호 입력을 먼저 생성한다. 독립 추출한 1·2·3·4배 재무 규모를 적용해 고가 차량도 감당 가능한 신규 상황을 포함한다. 소득 상한은 월 6천만원이며 모든 재무 입력 6개와 저축·비상자금·여유자금 맥락을 같은 배율로 조정한다. 실제 사용자 소득 분포를 추정한 값은 아니다.
- 기존 품질 규칙과 확률 선택을 그대로 적용한 뒤 부족한 라벨이 선택된 행만 채택한다. 차량을 강제로 지정하거나 선택 후 선호를 변경하지 않는다.
- 채택 과정에서 학습 클래스 분포는 의도적으로 달라진다. 이 보완본은 실제 시장 점유율이나 자연 발생 선택 빈도 추정용이 아니다.
- 신규 273행은 모두 서로 다른 입력이다. 기존 입력 복제·검증/평가 이동 없이 추가했고, 평가 전용 선호 조합은 학습에서 계속 제외한다.
- 최소 정원, 구매자금, 월 상환·유지비, 추가 여유자금, 선호 우선순위, 비교 후보 개수는 기존 독립 감사기로 전체 행을 다시 검사한다.

전체 데이터는 `combined_training.csv`, 추가분은 `supplement_training.csv`, 차량별 수량은 `label_coverage.csv`에 있다. `coverage_report.json`은 생성 설정과 원본 해시, `coverage_validation.json`은 기존 행 보존·중복·차량 라벨 분리 검사, `validation_report.json`은 전체 품질 감사 결과다. 원래 재무 가정·제원 근거·선호 타협 정책은 `../preference-quality-v1/README.md`와 동일하다.

PowerShell에서 프로젝트 루트를 기준으로 실행한다.

```powershell
$env:PYTHONPATH='.;ml'
python -m tools.data.households.supplement_vehicle_coverage
python -m tools.data.households.verify_vehicle_coverage
python -c "from tools.data.households.audit_quality_training import audit; from tools.data.households.supplement_vehicle_coverage import DESTINATION; audit(DESTINATION)"
```

학습 로더 연결과 실제 모델 학습은 별도 작업이다.
