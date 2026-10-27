package com.kh.back.admin.dto;

import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.Setter;

/**
 * 7단계: 관리자 회원 목록의 DB 한 줄 (users + user_profiles + 구글 연결 · 로그인된 기기 수).
 * 화면으로 보낼 때는 AdminMemberResponse 로 바꾼다 (이메일 가리기 · 나이대 계산).
 */
@Getter
@Setter
public class AdminMemberRow {

    private Long id;
    private String email;
    private String nickName;
    private String role;
    private LocalDateTime createdAt;
    private boolean hasPassword;   // 이메일 · 비밀번호로 가입했는지 (구글 전용이면 false)
    private boolean hasGoogle;     // 구글 계정이 연결됐는지
    private LocalDate birthDate;   // 없을 수 있음 (10-22 ~ 10-26 구글 가입 등)
    private String gender;
    private int activeSessions;    // 로그인된 기기 수 (기한이 남은 refresh token)
    private LocalDateTime lastUsedAt; // 로그인된 기기 중 가장 최근 사용 시각 (모두 로그아웃했으면 null)
}
