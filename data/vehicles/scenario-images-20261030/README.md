# 시나리오 카탈로그 이미지 보완

현재 모델 카탈로그 96모델·308사양 중 이미지 연결이 없던 12모델을 보완했다.

골프, 골프 GTI, 시에나, 알파드, 무쏘, 무쏘 EV, 카이엔, 허머 EV SUV,
PV5 패신저, 캐니언, 시에라, 308 SMART HYBRID의 제조사 공개 대표 사진이다.
골프와 GTI, 무쏘와 무쏘 EV는 각각 별도의 모델 사진으로 연결한다.

- `sources.json`: 제조사 출처 페이지와 원본 이미지 URL
- `manifest.json`: 원본·산출물 SHA-256, 크기, 처리 방식, 확인일
- 프론트 자산: `front/public/images/recommendations/scenario-models-20261030/`
- 등록 목록: `front/src/features/vehicle/scenarioModelImages.js`

재생성: 저장소 루트에서 `python tools/data/vehicles/register_scenario_images.py`.
원본 종횡비를 보존하며 WebP로 변환한다. 차량 외형을 생성하거나 변경하지 않는다.
관리자가 업로드한 사진과 이미지 제거 설정은 기존 우선순위를 유지한다.
