-- 동시 저장 확인용 시각은 마이크로초까지 보존한다. 적용된 V10은 변경하지 않는다.
ALTER TABLE user_current_tastes MODIFY saved_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
 COMMENT '명시적으로 저장할 때만 갱신';
