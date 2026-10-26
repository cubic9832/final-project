package com.kh.back.admin.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.Setter;

/**
 * 7단계: 운영 로그 한 줄 (admin_audit_logs + 관리자 · 대상 닉네임).
 * 닉네임은 기록에 저장하지 않고 지금 users 에서 읽는다 → 탈퇴했으면 null (화면에서 "탈퇴한 회원")
 */
@Getter
@Setter
public class AdminAuditLogResponse {

    private Long id;
    private Long actorId;
    private String actorNickName;
    private String action;      // ROLE_CHANGE
    private String targetType;  // MEMBER
    private Long targetId;
    private String targetNickName;
    private String detail;      // 예: USER → ADMIN
    private LocalDateTime createdAt;
}
