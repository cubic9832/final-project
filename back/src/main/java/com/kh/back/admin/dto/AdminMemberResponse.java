package com.kh.back.admin.dto;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Period;

/**
 * 7단계: 관리자 회원 목록 1명.
 * 이메일은 가려서 보낸다 (예: st****@example.com) — 관리 화면에서도 필요한 만큼만 보여 준다.
 * 생년월일 대신 나이대만, 비밀번호 · 전화번호는 보내지 않는다.
 *
 * @param loginMethod EMAIL · GOOGLE · BOTH (이메일 가입 후 구글 연결)
 * @param lockedMinutes 로그인 5번 실패로 잠긴 남은 분 (0 이면 잠금 없음, 보완 6)
 */
public record AdminMemberResponse(Long id, String nickName, String emailMasked, String role,
                                  LocalDateTime joinedAt, String loginMethod, String ageBand, String gender,
                                  int activeSessions, LocalDateTime lastUsedAt, long lockedMinutes) {

    public static AdminMemberResponse from(AdminMemberRow row, long lockedMinutes) {
        return new AdminMemberResponse(row.getId(), row.getNickName(), maskEmail(row.getEmail()), row.getRole(),
                row.getCreatedAt(), loginMethod(row), ageBand(row.getBirthDate()), row.getGender(),
                row.getActiveSessions(), row.getLastUsedAt(), lockedMinutes);
    }

    private static String loginMethod(AdminMemberRow row) {
        if (row.isHasPassword() && row.isHasGoogle()) return "BOTH";
        return row.isHasGoogle() ? "GOOGLE" : "EMAIL";
    }

    // 만 나이로 나이대 (10대 ~ 50대 이상). 생년월일이 없으면 null → 화면에서 "미입력"
    static String ageBand(LocalDate birthDate) {
        if (birthDate == null) return null;
        int age = Period.between(birthDate, LocalDate.now()).getYears();
        if (age >= 50) return "50대 이상";
        return (age / 10 * 10) + "대";
    }

    // 아이디 앞 2글자만 보이고 나머지는 * (최대 4개) — 도메인은 그대로
    static String maskEmail(String email) {
        int at = email.indexOf('@');
        if (at <= 0) return "****";
        String id = email.substring(0, at);
        String shown = id.length() <= 2 ? id.substring(0, 1) : id.substring(0, 2);
        return shown + "*".repeat(Math.min(4, Math.max(1, id.length() - shown.length()))) + email.substring(at);
    }
}
