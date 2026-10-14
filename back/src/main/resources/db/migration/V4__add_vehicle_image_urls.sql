-- 공식 제조사 페이지의 모델 대표 이미지 URL (확인일: 2026-10-13).
-- 이미지 파일은 저장하지 않는다. 트림/색상별 실물 사진이 아닌 모델 대표 이미지다.
-- 이미 등록된 이미지와 사용자 차량 데이터는 유지한다.

UPDATE vehicles v
JOIN brands b ON b.id = v.brand_id
SET v.image_url = 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/represent/krja305/morning_s_a2g.png'
WHERE b.name = '기아' AND v.name = '모닝'
  AND v.is_example = TRUE AND v.condition_code = 'NEW'
  AND (v.image_url IS NULL OR v.image_url = '');

UPDATE vehicles v
JOIN brands b ON b.id = v.brand_id
SET v.image_url = 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/represent/krtm311/ray_s_ud.png'
WHERE b.name = '기아' AND v.name = '레이'
  AND v.is_example = TRUE AND v.condition_code = 'NEW'
  AND (v.image_url IS NULL OR v.image_url = '');

UPDATE vehicles v
JOIN brands b ON b.id = v.brand_id
SET v.image_url = 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/represent/krdl308/k5_s_c7s.png'
WHERE b.name = '기아' AND v.name = 'K5'
  AND v.is_example = TRUE AND v.condition_code = 'NEW'
  AND (v.image_url IS NULL OR v.image_url = '');

UPDATE vehicles v
JOIN brands b ON b.id = v.brand_id
SET v.image_url = 'https://org1.hyundai.com/content/dam/hyundai/kr/ko/images/brand/heritage/heritage-the-new-avante-hybrid-640x412.jpg'
WHERE b.name = '현대' AND v.name = '아반떼 하이브리드'
  AND v.is_example = TRUE AND v.condition_code = 'NEW'
  AND (v.image_url IS NULL OR v.image_url = '');
