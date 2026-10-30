-- 8단계: 1:1 상담 채팅 (회원 ↔ 관리자). 강의 샘플 step4--features 의 chat_room · chat_message 를 1:1 상담에 맞게 바꿨다
-- 샘플과 다른 점: 방은 회원 1명당 1개(user_id UNIQUE), 참여자 표(chat_room_member) 대신 "그 회원 + 맡은 관리자"
-- 번호: develop 의 마지막이 V21(admin_accounts) 이라 V22

-- 상담방 (회원 1명당 1개 — 종료 후 다시 상담하면 같은 방을 대기로 되돌린다)
CREATE TABLE chat_room (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    -- 상담을 받는 회원 (임시: 탈퇴하면 상담 기록도 같이 지운다 — 탈퇴 후 기록을 남기는 방식은 11-03 이후 정한다)
    user_id BIGINT NOT NULL,
    -- WAITING(대기) · ACTIVE(진행 중) · CLOSED(종료)
    status VARCHAR(20) NOT NULL DEFAULT 'WAITING',
    -- 맡은 관리자 (대기 · 담당자가 탈퇴하면 NULL)
    assigned_admin_id BIGINT NULL,
    -- 마지막 메시지 시각 (관리자 목록을 최근 순으로)
    last_message_at DATETIME NULL,
    -- 상담 제한이 끝나는 시각 (욕설 등으로 관리자가 제한하면 이때까지 새 상담 불가, 제한한 적 없으면 NULL)
    restricted_until DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_chat_room_user UNIQUE (user_id),
    CONSTRAINT chk_chat_room_status CHECK (status IN ('WAITING', 'ACTIVE', 'CLOSED')),
    CONSTRAINT fk_chat_room_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_chat_room_admin FOREIGN KEY (assigned_admin_id) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_chat_room_status (status, last_message_at)
);

-- 메시지
CREATE TABLE chat_message (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    room_id BIGINT NOT NULL,
    -- USER(회원) · ADMIN(상담원) · SYSTEM(연결 · 넘김 · 종료 안내)
    sender_type VARCHAR(20) NOT NULL,
    -- 보낸 사람 (SYSTEM 이거나 보낸 관리자가 탈퇴하면 NULL)
    sender_id BIGINT NULL,
    content VARCHAR(1000) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_chat_message_sender CHECK (sender_type IN ('USER', 'ADMIN', 'SYSTEM')),
    CONSTRAINT fk_chat_message_room FOREIGN KEY (room_id) REFERENCES chat_room (id) ON DELETE CASCADE,
    CONSTRAINT fk_chat_message_sender FOREIGN KEY (sender_id) REFERENCES users (id) ON DELETE SET NULL,
    -- "이 방의 최근 메시지" 를 빠르게 (샘플과 같음)
    INDEX idx_chat_message_room (room_id, id)
);
