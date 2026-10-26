-- 7단계: 관리자 작업 기록 (운영 로그). 지금은 총관리자의 관리자 권한 주기 · 빼기를 남긴다.
-- 이미 적용된 V1 ~ V12 는 고치지 않는다.
-- 이름 · 이메일은 저장하지 않고 회원 번호만 남긴다 (화면에서 users 와 이어 붙여 보여 주고, 탈퇴하면 번호도 NULL)

CREATE TABLE admin_audit_logs (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    -- 작업한 관리자 (탈퇴하면 NULL — 기록은 남긴다)
    actor_id BIGINT NULL,
    -- 작업 종류: ROLE_CHANGE (나중에 잠금 해제 · 차량 수정 등도 같은 표에)
    action VARCHAR(30) NOT NULL,
    -- 대상 종류와 번호: MEMBER + 회원 번호 (대상이 탈퇴하면 번호는 그대로 두고 화면에서 "탈퇴한 회원")
    target_type VARCHAR(20) NOT NULL,
    target_id BIGINT NULL,
    -- 바뀐 내용 (예: USER → ADMIN)
    detail VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_admin_audit_logs_actor FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_admin_audit_logs_created_at (created_at)
);
