-- 보완 11: 관리자 권한을 회원 표(users)에서 따로 떼어 낸다.
-- 로그인은 그대로 users 하나로 하고(일반 로그인 창), 이 표에 있는 회원만 관리자 · 총관리자다. 없으면 일반 회원(USER).
-- 번호: develop 은 V14 까지지만 main 에 V15 ~ V17 이 있어 합칠 때 겹치지 않게 V18 을 쓴다.
-- 총관리자는 화면에서 만들 수 없고 DB(또는 서버 시드 AdminAccountSeeder)로만 넣는다.

CREATE TABLE admin_accounts (
    -- 회원 번호 (회원 1명당 1줄, 탈퇴하면 같이 지운다)
    user_id BIGINT NOT NULL PRIMARY KEY,
    -- ADMIN(관리자) · SUPER_ADMIN(총관리자)
    role VARCHAR(20) NOT NULL,
    -- 관리자로 지정한 총관리자 (DB · 시드로 넣었거나 지정한 사람이 탈퇴하면 NULL)
    granted_by BIGINT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_admin_accounts_role CHECK (role IN ('ADMIN', 'SUPER_ADMIN')),
    CONSTRAINT fk_admin_accounts_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_admin_accounts_granted_by FOREIGN KEY (granted_by) REFERENCES users (id) ON DELETE SET NULL
);

-- 지금까지 users.role 에 있던 관리자를 옮기고, users.role 은 모두 USER 로 맞춘다 (컬럼은 남겨 두지만 더는 권한으로 쓰지 않는다)
INSERT INTO admin_accounts (user_id, role)
SELECT id, role FROM users WHERE role IN ('ADMIN', 'SUPER_ADMIN');

UPDATE users SET role = 'USER' WHERE role IN ('ADMIN', 'SUPER_ADMIN');
