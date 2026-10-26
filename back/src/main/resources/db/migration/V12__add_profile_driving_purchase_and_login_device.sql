-- 6단계 마이페이지: 개인 정보에 운전 경력 · 구매 예정 시기, 로그인된 기기 목록에 쓸 칸을 더한다.
-- 이미 적용된 V1 ~ V11 은 고치지 않는다.

-- 운전 경력 · 구매 예정 시기 (둘 다 선택 항목, 비어 있으면 NULL)
ALTER TABLE user_profiles
    ADD COLUMN driving_experience VARCHAR(20) NULL COMMENT '운전 경력: NONE · UNDER_1Y · YEARS_1_3 · OVER_3Y',
    ADD COLUMN purchase_timing VARCHAR(20) NULL COMMENT '구매 예정 시기: WITHIN_3M · WITHIN_6M · WITHIN_1Y · UNDECIDED';

-- 로그인된 기기: refresh token 1행 = 로그인 중인 기기 1개
-- IP 주소는 개인정보라 저장하지 않고, 브라우저 · 운영체제 이름만 남긴다
ALTER TABLE refresh_token
    ADD COLUMN device VARCHAR(100) NULL COMMENT '브라우저 · 운영체제 (예: Chrome · Windows)',
    ADD COLUMN logged_in_at DATETIME NULL COMMENT '처음 로그인한 시각. 재발급(교체) 때도 그대로 넘긴다';
