# 신규 차량 사진·상세 정보 (2026-10-28)

`ml/test` 작업 결과입니다. 기존 차량 자료에 추가한 **23개 모델군, 41개 구성**을 대상으로 합니다.

- `image-manifest.json`: 23개 대표 사진의 공식 페이지·원본 URL·보관 방식·원본 및 최종 파일 해시·투명 영역·화면 배치.
- `vehicle-details.json`: 41개 구성의 공개 상세 제원, 적용 연식, 출처·원문 파일 해시·주의 사항.
- `sources/`: 제조사·공식 딜러 원문 및 실제 브라우저 제원 패널. 실패한 요청도 기록되어 있으며 성공한 대체 출처와 구분됩니다.
- `images/`: 다운로드한 원본 및 공식 이미지가 정상 표시된 브라우저 화면 캡처.
- `cutouts/`: 내장 imagegen 도구로 배경을 추출한 PNG. 도구 기본 저장 위치에서 프로젝트로 복사했습니다.
- `image-review.html`: 23개 사진 검수용 갤러리. 프로젝트 루트에서 로컬 HTTP 서버로 열 수 있습니다.
- `image-review-*.png`, `ui-specifications.png`: 전체 사진 및 실제 추천 카드의 브라우저 검수 화면.

## 등록 방식

기존 `build_recommendation_images.image_style`의 알파 경계·차량 크기·접지선 계산을 그대로 사용합니다. 제조사 투명 원본 9개(페라리 6개, 포르쉐 3개)는 형식만 변환했습니다. 나머지 14개는 원본 차량의 형태·색상·장비·각도를 유지하도록 imagegen으로 배경을 추출하고 무손실 투명 WebP로 저장했습니다. 포르쉐는 제조사 정면 투명 이미지를 사용하며 다른 모델은 전면 사선 사진입니다.

사진은 **모델군 대표 사진**입니다. M2/M240i, M4/420i, i4/420i, GT3/GTS 등 모든 세부 트림 외형이 같다는 의미가 아닙니다. 관리자 업로드 사진과 사진 삭제 설정은 계속 우선합니다.

MINI·마세라티 2개는 직접 파일 요청이 제한되었지만 브라우저에서 공식 이미지가 정상 표시되어 해당 화면을 보관했습니다. 인증·로봇 확인을 우회하지 않았습니다.

## 제원 적용 범위

제원은 추천 카드의 상세 보기용 자료입니다. 차량 ID뿐 아니라 브랜드·모델·트림·연식이 일치할 때만 표시합니다. 기존 학습 카탈로그·백만 건 합성 데이터·모델 번들·정원 검증 상태를 변경하지 않았습니다.

모든 트림의 모든 항목을 확인했다는 뜻은 아닙니다. 특히 BMW 일부 트림의 치수·정원, 국내 인증이 확인되지 않은 고급 차량의 공인 연비는 임의로 채우지 않습니다. 페라리 공식 딜러의 국제 사양, 포르쉐 한국 구성기의 EU/WLTP 참조 사양, 람보르기니 국제 제원은 국내 인증 제원과 구분합니다. 마세라티는 한국 페이지의 **2026년형 490PS/550PS**를 각각 저장했습니다.

포르쉐 원문의 중복 엔진 출력(485/495PS), BMW M440i의 토크 환산 차이, Z4의 제원표·FAQ 가속 시간 차이는 주석이나 충돌 표시로 남겼습니다. 하이브리드 엔진 출력과 시스템 합산 출력을 합치지 않습니다. Roma Spider는 공식 딜러의 Past Models 분류도 보존합니다. 가격과 국내 주문 가능 여부를 이번 제원 수집만으로 확정하지 않습니다.

## 재생성

원문과 검수한 cutouts가 있는 상태에서 프로젝트 루트에서 실행합니다.

```powershell
python tools/data/vehicles/build_new_vehicle_details.py
python tools/data/vehicles/register_new_vehicle_images.py
cd front
npm test
npm run build
npm run lint
```

원본 수집 도구는 `collect_new_vehicle_details.py`, `build_new_vehicle_assets.py`, `collect_remaining_vehicle_assets.py`, `download_vehicle_asset_alternatives.py`입니다. 네트워크 실패 기록을 최종 등록 자료로 사용하지 않습니다.

## imagegen 프롬프트

내장 도구를 사용했습니다. 8개 초기 편집의 프롬프트 요약은 `edited-images.json`, 이후 6개의 생성 파일은 `edited-images-extra.json`, `edited-images-final.json`에 기록했습니다.

후속 2개(BMW 8, Roma Spider):

> Remove only the background from this official car photograph. Preserve this exact vehicle, body shape, roof state, paint color, wheels, badges, proportions and viewing angle. Do not redesign or add optional equipment. Isolate the entire car, upright wheels level, centered with generous transparent margins in a 1536x1024 canvas, matching a premium vehicle recommendation card product cutout. No text, no scenery, no floor, no opaque background. Keep only a subtle translucent contact shadow.

후속 4개(Z4, MINI, 마세라티 2개):

> Extract only the main central car from this official reference photograph. Remove the scenery, mirrors/reflections showing other cars, people, and screen borders. Preserve the exact main vehicle design, proportions, roof-open state, paint, wheels, grille, lights, badges and original viewing angle. Do not change equipment or redesign the vehicle. Center the entire car upright with wheels level and generous transparent margins on a 1536x1024 canvas, like existing premium vehicle recommendation card cutouts. Transparent background with only a very subtle translucent contact shadow. No text or floor.
