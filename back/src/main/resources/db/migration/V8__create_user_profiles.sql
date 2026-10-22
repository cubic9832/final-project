-- 보완 5: 회원가입 개인 정보 (전화번호 · 생년월일 · 성별)
-- users 는 조원 기능도 쓰는 공용 테이블이라 손대지 않고, 개인 정보만 따로 둔다 (회원 1명당 1행)
CREATE TABLE user_profiles (
    -- users.id 와 1:1. 회원이 삭제(탈퇴)되면 이 행도 함께 삭제된다
    user_id BIGINT NOT NULL PRIMARY KEY,
    -- 연락용 전화번호. 숫자만 저장 (예: 01012345678). 인증하지 않은 번호라 중복 금지는 걸지 않는다
    phone VARCHAR(20),
    -- 생년월일. 가입 나이 제한(만 18세 이상)과 연령대 통계에 쓴다
    birth_date DATE,
    -- 성별: MALE · FEMALE · NONE(선택 안 함)
    gender VARCHAR(10),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_profiles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
