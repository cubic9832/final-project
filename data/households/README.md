# 공식 가구 재무 통계

개인별 가상 재무 데이터를 생성하기 위한 실제 통계 기준값이다. 개인별 금융 기록이나 대출 연체·상환 결과 데이터는 아니다.

## 확보 자료

- [한국은행 2025년 가계금융복지조사](https://www.bok.or.kr/portal/bbs/B0000501/view.do?depth=201264&menuNo=201264&nttId=10094917&oldMenuNo=201150&programType=newsData&relate=Y)의 공식 XLSX: 2024·2025년 조사, 각각 38개 가구 특성 집단, 21개 기본 지표.
- [2025년 4분기 가계동향조사 공식 PDF](https://sri.kostat.go.kr/boardDownload.es?bid=214&list_no=443727&seq=1)의 표 5·6: 소득 5분위별 월평균 소득·소비·처분가능소득·흑자액과 소비 항목별 지출.

다운로드 원본은 `sources/`, URL·SHA256·파일 크기는 `source-manifest.json`에 보관한다. 확인일은 2026-10-14이며 모든 최신 분기 자료를 수집한 것은 아니다. KOSIS API는 인증키가 필요하므로 이번에는 공식 다운로드 파일을 사용했다.

## CSV

| 파일 | 행 수 | 내용 |
| --- | ---: | --- |
| csv/household-financial-profiles.csv | 76 | 연도·가구 특성별 자산, 저축, 부채, 소득, 원리금상환 평균 |
| csv/household-financial-metrics.csv | 1,596 | 위 기본 지표를 세로로 정리, 원래 값·단위·원본 셀 포함 |
| csv/household-income-expenditure-quintiles.csv | 5 | 2025Q4 소득 분위별 월평균 소득과 지출 |
| csv/household-income-expenditure-metrics.csv | 165 | PDF 지표별 값·전년 동기 변화·페이지·상대표준오차 주의 표시 |

UTF-8 BOM CSV이며 빈 칸은 결측값이다. 금융 통계의 `_won`은 원, `_pct`는 %, 가구원 수는 명, 연령은 세다. 소비 CSV의 금액 열은 모두 원/월이며 `가구원수(명)`, `가구주연령(세)`, `흑자율(%)`, `평균소비성향(%)`은 열 이름의 단위를 따른다. 세로형 파일은 `normalized_unit`으로 단위를 명시한다. 원본의 만원은 10,000배, 천원은 1,000배 변환한다.

## 해석과 구현 주의

- 가계금융복지조사의 자산·부채는 조사연도 3월 31일 기준이다. 연간 소득·비소비지출·원리금상환은 전년도 기준이다. `monthly_*_derived_won`은 연간 평균을 12로 나눈 파생값이며 실제 월별 관측치가 아니다.
- 소득은 가구 소득이다. 개인의 월 실수령액으로 바로 입력하면 안 된다.
- 금융자산에는 전월세보증금이 포함된다. 적립·예치식 저축도 모두 즉시 인출할 수 있는 구매 자금으로 간주하면 안 된다. 총부채에는 임대인이 반환해야 할 임대보증금도 포함된다.
- 가구 특성별 평균에는 해당 자산·부채가 없는 가구도 포함된다. 연령 등의 하위 집단은 부모 집단과 겹친다(`overlapping_subgroup`). 76행은 76명의 실제 사람을 뜻하지 않는다.
- 두 조사의 소득 1분위 등을 같은 가구 집단으로 결합하지 않는다. 조사 시점과 모집단·분위 구성이 다르며 개인별 결합 키가 없다.
- 평균만으로 개인별 분포나 소득·부채·소비의 상관관계를 복원할 수 없다. 가상 데이터를 만들 때 분산·상관관계 가정과 생성 규칙을 별도로 기록해야 한다.
- PDF는 천원 단위 반올림으로 합계와 구성 항목 간 차이가 생길 수 있다. 높은 상대표준오차 표시가 있는 값은 세로형 CSV에 기록했다.
- 이 자료로 예산 계산과 시뮬레이션의 기준값은 구현할 수 있다. 실제 연체 확률이나 대출 승인 모델의 성능을 입증할 수는 없다.

## 재현

`python -m tools.data.statistics.download_official_statistics`는 공식 파일을 내려받고 출처 정보를 저장한다(BeautifulSoup 필요). `python -m tools.data.statistics.extract_household_statistics`는 openpyxl·pypdf로 숫자와 근거를 JSON에 추출한다. `node tools/data/csv/exportHouseholdCsv.mjs`는 Node.js 기본 기능으로 CSV를 작성한다.
