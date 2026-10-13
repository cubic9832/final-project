-- 제조사 공식 가격표 확인일: 2026-10-13. 신차 기본 트림 14건.
-- 가격: 원, 선택 옵션/취득세/등록비/탁송료 제외. 하이브리드는 세제혜택 후 가격.
-- 연비: 기본 휠 기준 복합 km/L, 빌트인 캠 옵션 제외.
-- 연식이 가격표에서 확인되지 않은 레이/K5는 NULL로 보존한다.
-- 실매물/실시간 견적이 아닌 참고용 시드이므로 is_example = TRUE.
-- ID를 고정하지 않고 제조사명으로 FK를 연결하며 기존 차량 정보는 덮어쓰지 않는다.

INSERT INTO brands (name)
SELECT seed.name
FROM (SELECT '현대' AS name UNION ALL SELECT '기아') AS seed
WHERE NOT EXISTS (SELECT 1 FROM brands existing WHERE existing.name = seed.name);

INSERT INTO vehicles (
 brand_id, name, trim_name, model_year, condition_code, class_code, fuel_code,
 seating_capacity, price, efficiency_value, efficiency_unit, image_url,
 source_name, source_url, is_example
)
SELECT brand.id, seed.name, seed.trim_name, seed.model_year, 'NEW', seed.class_code,
 seed.fuel_code, seed.seating_capacity, seed.price, seed.efficiency_value, 'km/L',
 NULL, seed.source_name, seed.source_url, TRUE
FROM (
SELECT '현대' AS brand_name, '아반떼 하이브리드' AS name, '스마트 · 1.6 HEV · 16인치' AS trim_name, 2026 AS model_year, 'COMPACT_SEDAN' AS class_code, 'HYBRID' AS fuel_code, 5 AS seating_capacity, 25550000 AS price, 21.1 AS efficiency_value, '현대자동차 2026 아반떼 하이브리드 가격표' AS source_name, 'https://www.hyundai.com/contents/repn-car/catalog/avante-hybrid-2026-price.pdf' AS source_url
 UNION ALL
 SELECT '현대', '아반떼 하이브리드', '모던 라이트 · 1.6 HEV · 16인치', 2026, 'COMPACT_SEDAN', 'HYBRID', 5, 25820000, 21.1, '현대자동차 2026 아반떼 하이브리드 가격표', 'https://www.hyundai.com/contents/repn-car/catalog/avante-hybrid-2026-price.pdf'
 UNION ALL
 SELECT '현대', '아반떼 하이브리드', '모던 · 1.6 HEV · 16인치', 2026, 'COMPACT_SEDAN', 'HYBRID', 5, 28300000, 21.1, '현대자동차 2026 아반떼 하이브리드 가격표', 'https://www.hyundai.com/contents/repn-car/catalog/avante-hybrid-2026-price.pdf'
 UNION ALL
 SELECT '현대', '아반떼 하이브리드', '인스퍼레이션 · 1.6 HEV · 17인치', 2026, 'COMPACT_SEDAN', 'HYBRID', 5, 31610000, 19.2, '현대자동차 2026 아반떼 하이브리드 가격표', 'https://www.hyundai.com/contents/repn-car/catalog/avante-hybrid-2026-price.pdf'
 UNION ALL
 SELECT '현대', '아반떼 하이브리드', 'N Line · 1.6 HEV · 18인치', 2026, 'COMPACT_SEDAN', 'HYBRID', 5, 32310000, 18.5, '현대자동차 2026 아반떼 하이브리드 가격표', 'https://www.hyundai.com/contents/repn-car/catalog/avante-hybrid-2026-price.pdf'
 UNION ALL
 SELECT '기아', '모닝', '트렌디 · 1.0 가솔린 · 14인치', 2027, 'MINI', 'GASOLINE', 5, 14210000, 14.7, '기아 모닝 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_morning.pdf'
 UNION ALL
 SELECT '기아', '모닝', '프레스티지 · 1.0 가솔린 · 14인치', 2027, 'MINI', 'GASOLINE', 5, 16010000, 14.7, '기아 모닝 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_morning.pdf'
 UNION ALL
 SELECT '기아', '모닝', '시그니처 · 1.0 가솔린 · 16인치', 2027, 'MINI', 'GASOLINE', 5, 18160000, 14.7, '기아 모닝 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_morning.pdf'
 UNION ALL
 SELECT '기아', '모닝', 'GT-Line · 1.0 가솔린 · 16인치', 2027, 'MINI', 'GASOLINE', 5, 19110000, 14.7, '기아 모닝 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_morning.pdf'
 UNION ALL
 SELECT '기아', '레이', '트렌디 · 1.0 가솔린 · 14인치', NULL, 'MINI', 'GASOLINE', 5, 15550000, 12.9, '기아 레이 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_ray.pdf'
 UNION ALL
 SELECT '기아', '레이', '프레스티지 · 1.0 가솔린 · 14인치', NULL, 'MINI', 'GASOLINE', 5, 18150000, 12.9, '기아 레이 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_ray.pdf'
 UNION ALL
 SELECT '기아', '레이', '시그니처 · 1.0 가솔린 · 15인치', NULL, 'MINI', 'GASOLINE', 5, 19550000, 12.6, '기아 레이 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_ray.pdf'
 UNION ALL
 SELECT '기아', '레이', 'X-Line · 1.0 가솔린 · 15인치', NULL, 'MINI', 'GASOLINE', 5, 20600000, 12.6, '기아 레이 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_ray.pdf'
 UNION ALL
 SELECT '기아', 'K5', '프레스티지 · 1.6 가솔린 터보 · 17인치', NULL, 'MIDSIZE_SEDAN', 'GASOLINE', 5, 29730000, 13.7, '기아 K5 가격표 (2026-10)', 'https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_k5.pdf'
) AS seed
JOIN brands brand ON brand.name = seed.brand_name
WHERE NOT EXISTS (
 SELECT 1 FROM vehicles existing
 WHERE existing.brand_id = brand.id
   AND existing.name = seed.name
   AND existing.trim_name <=> seed.trim_name
   AND existing.model_year <=> seed.model_year
   AND existing.condition_code = 'NEW'
   AND existing.fuel_code = seed.fuel_code
);
