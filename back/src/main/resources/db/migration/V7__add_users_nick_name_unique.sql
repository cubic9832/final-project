-- 닉네임 중복 금지 (보완 3 · 보완 목록 ⑧, 회의 2026-10-19: 나중에 채팅 기능을 고려해 중복 금지)
-- 1) 이미 같은 닉네임이 있는 회원은 나중에 가입한 쪽 닉네임 뒤에 "_회원번호" 를 붙여 겹치지 않게 정리한다
--    (각자 로컬 DB 에 테스트 회원이 겹쳐 있어도 이 파일이 실패하지 않게)
-- 2) users.nick_name 에 UNIQUE 를 건다. nick_name 이 NULL 인 회원은 여러 명이어도 된다 (MySQL UNIQUE 규칙)

-- 1) 겹치는 닉네임 정리: 같은 닉네임 중 id 가 가장 작은 회원만 그대로 두고, 나머지는 "닉네임_id"
UPDATE users u
JOIN (
  SELECT u1.id
  FROM users u1
  JOIN users u2 ON u1.nick_name = u2.nick_name AND u1.id > u2.id
  GROUP BY u1.id
) dup ON dup.id = u.id
SET u.nick_name = CONCAT(LEFT(u.nick_name, 40), '_', u.id);

-- 2) 같은 닉네임 중복 방지
ALTER TABLE users ADD UNIQUE KEY uq_users_nick_name (nick_name);
