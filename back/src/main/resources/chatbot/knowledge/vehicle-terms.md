# 자동차 용어 설명 자료

## MPV · 미니밴 · 승합
MPV는 Multi-Purpose Vehicle, 즉 다목적 차량이다. 사람과 짐을 싣는 실내 공간의 활용에 중점을 둔 차를 설명할 때 쓴다. 카니발은 이해를 돕는 MPV 예시다. SUV와 모두 공간 활용에 관심을 두지만, MPV는 여러 사람이 편하게 타는 실내 구성을 설명할 때 특히 자주 쓰인다. 특정 모델의 좌석 수나 슬라이딩 도어 여부는 연식과 트림을 따로 확인해야 한다. 이 서비스에서 표시하는 MPV·승합 분류만으로 법적인 승용/승합 등록 구분을 확정하지 않는다.
근거: 기아의 카니발 MPV 소개 https://www.kiamedia.com/us/en/media/pressreleases/21841/2025-kia-carnival-mpv-redefined-elevating-multi-purpose-appeal-with-hybrid-power-sophisticated-desig

## MIDSIZE_SUV · 중형 SUV
MIDSIZE_SUV는 서비스의 차량 크기·차체 분류 코드이며 한국어로 중형 SUV라는 뜻이다. MIDSIZE는 중간 크기, SUV는 Sport Utility Vehicle의 약자다. 취향 결과에서 기아 쏘렌토 카드에 이 분류가 붙으면 쏘렌토를 중형 SUV 그룹으로 보여주고 있다는 의미다. MPV는 여러 사람과 짐을 위한 실내 활용을 강조하는 분류이고, 중형 SUV는 SUV 중에서의 크기 분류다. 분류 이름만으로 사륜구동·험로 주행 능력·좌석 수를 보장하지 않는다. 고정된 법정 크기 기준으로 안내하지 않는다.
근거: 프로젝트 차량 분류 매핑과 취향 테스트 대표 차량 카탈로그.

## SUV · 스포츠 유틸리티 차량
SUV는 Sport Utility Vehicle의 약자다. 쉽게 말해 승용차의 편의와 공간 활용을 함께 고려하는 차체 형태를 가리킨다. 차체 높이와 적재 공간을 비교할 때 쓰는 말이며, SUV라는 이름만으로 모든 차가 사륜구동이거나 오프로드용이라는 뜻은 아니다. MPV와의 차이는 특정 차량의 실내 구성·적재 방식·제원으로 비교해야 한다.

## SUBCOMPACT_SUV · COMPACT_SUV · LARGE_SUV
프로젝트에서 SUBCOMPACT_SUV는 소형 SUV, COMPACT_SUV는 준중형 SUV, LARGE_SUV는 대형 SUV로 표시한다. SUV 안에서 크기를 구분하기 위한 서비스 분류다. MIDSIZE_SUV는 이들과 비교하는 중형 SUV다. 같은 크기 그룹이어도 실내 공간·좌석 수·차체 길이가 다를 수 있어 실제 모델 제원을 확인해야 한다. SUV 크기는 법정 차급과 동일하다고 가정하지 않는다.
근거: front/src/features/vehicle/vehicleApi.js의 classLabels.

## SEDAN · COMPACT_SEDAN · MIDSIZE_SEDAN · FULLSIZE_SEDAN
세단은 일반적으로 탑승 공간과 뒤쪽 트렁크가 구분되는 승용차 차체 형태를 말한다. 프로젝트에서 COMPACT_SEDAN은 준중형 세단, MIDSIZE_SEDAN은 중형 세단, FULLSIZE_SEDAN은 대형 세단이다. 취향 테스트의 아반떼와 K5는 각각 준중형·중형 세단을 이해하는 예시다. 같은 세단이라도 가격·실내 공간·유지비는 모델에 따라 달라진다.
근거: 프로젝트 차량 분류 매핑과 tasteVehicleExamples.js.

## MINI · 경차
프로젝트의 MINI는 경차 분류 코드다. 일상적으로 작은 차를 떠올릴 수 있지만, 모든 작은 자동차가 법적으로 경차인 것은 아니다. 취향 결과의 모닝·레이는 경차 예시로 제공된다. 세금·주차·통행료 혜택은 해당 차량과 현재 적용 조건을 따로 확인해야 하며 이 분류만 보고 혜택을 확정하지 않는다.
근거: 프로젝트 차량 분류 매핑과 대표 차량 예시.

## HYBRID · HEV · 하이브리드
하이브리드는 엔진과 전기 모터를 함께 활용하는 방식이다. 일반적인 HEV는 외부 충전기를 꽂는 방식 대신 주행 중 에너지 회수 등을 활용한다. 순수 전기차는 엔진 없이 전기 모터로 달리므로 구동 에너지를 보충하는 방식이 다르다. 하이브리드라고 무조건 연료비가 더 적다고 단정하지 않으며 주행 조건과 모델별 연비를 함께 본다.
근거: https://www.nhtsa.gov/vehicle-safety/electric-and-hybrid-vehicles

## PHEV · 플러그인 하이브리드
PHEV는 Plug-in Hybrid Electric Vehicle의 약자다. 엔진과 모터를 쓰면서 외부 충전기로 배터리를 충전할 수 있는 하이브리드다. 일반 HEV와는 외부 충전 가능 여부가 다르고, 순수 전기차와는 엔진도 사용한다는 차이가 있다. 실제 전기 주행 거리나 효율은 모델·충전 상태에 따라 달라진다.
근거: https://afdc.energy.gov/vehicles/electric-basics-phev

## MILD_HYBRID · 마일드 하이브리드
마일드 하이브리드는 전기 시스템이 엔진을 보조하는 방식이며 일반적인 풀 하이브리드와 작동 범위가 다르다. 일반적으로 전기 모터만으로 주행하는 능력이 제한적이거나 없다. HEV나 PHEV와 같다고 설명하지 않으며 세부 기능은 차종별로 확인한다.
근거: https://www.nhtsa.gov/vehicle-safety/electric-and-hybrid-vehicles

## ELECTRIC · EV · BEV · 전기차 · 전기 SUV
이 서비스의 ELECTRIC 분류는 배터리를 외부에서 충전하고 전기 모터로 주행하는 순수 전기차를 뜻한다. EV·BEV라는 표현도 사용한다. 하이브리드와 달리 이 분류의 순수 전기차에는 주행용 내연기관이 없다. 전기 SUV는 전기 구동 방식과 SUV 차체 형태를 함께 나타낸 말이다. 실제 주행 가능 거리와 충전 시간은 모델·환경에 따라 달라진다.
근거: https://www.nhtsa.gov/vehicle-safety/electric-and-hybrid-vehicles

## GASOLINE · 가솔린 · 휘발유 / DIESEL · 디젤 · 경유 / LPG
GASOLINE은 가솔린, 즉 휘발유 연료를 쓰는 분류이고 DIESEL은 디젤, 즉 경유 연료를 쓰는 분류다. LPG는 액화석유가스를 연료로 쓰는 분류다. 서로 다른 연료이므로 실제 차량에 맞는 연료를 확인해야 한다. 연료 종류만으로 성능·소음·유지비가 항상 유리하다고 단정하지 않는다.

## RUNNING_COST · 예상 월 유지비 · 월 유지비
예상 월 유지비는 차량을 계속 운행하고 보유하는 데 드는 비용을 월 단위로 추정한 값이다. 유류비·보험료·세금·정비비 등이 관련되며 실제 포함 항목은 화면의 산출 기준을 확인해야 한다. 차를 살 때 내는 차량 가격이나 대출 원금과 같은 뜻이 아니며, 월 할부금과도 구분한다. 개인의 실제 지출이나 확정 견적을 뜻하지 않는다.

## EFFICIENCY · 복합연비 · 연비
연비는 연료 사용량에 비해 얼마나 이동하는지를 나타내는 효율이다. km/L는 연료 1리터로 이동할 수 있는 거리 단위다. 복합연비는 정해진 시험 기준으로 도심·고속도로 조건 등을 반영한 수치이며 실제 운전 결과와 항상 같지는 않다. 전기차의 km/kWh는 전력 기준이므로 km/L와 숫자만 바로 비교하면 안 된다.
