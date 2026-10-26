package com.kh.back.auth.service;

import java.util.List;
import java.util.Locale;

/**
 * 회원가입 비밀번호 규칙 (보완 2 · 보완 목록 ⑥).
 * 길이 · 문자 종류는 SignupRequest 의 @Size · @Pattern 이 먼저 검사하고,
 * 여기서는 이메일과 함께 봐야 하거나 정규식으로 쓰기 어려운 규칙을 검사한다.
 * 프론트 front/src/features/auth/passwordPolicy.js 와 같은 규칙을 쓴다.
 */
public final class PasswordPolicy {

    // 너무 흔해서 금지하는 비밀번호 (소문자로 바꿔 포함 여부를 본다)
    private static final List<String> COMMON_WORDS = List.of(
            "password", "passw0rd", "p@ssw0rd", "qwerty", "1q2w3e4r", "iloveyou", "admin", "letmein", "welcome");

    // 이어진 문자로 볼 줄: 숫자 · 알파벳 순서, 키보드 가로줄 (거꾸로도 검사)
    private static final List<String> SEQUENCES = List.of(
            "0123456789", "abcdefghijklmnopqrstuvwxyz", "qwertyuiop", "asdfghjkl", "zxcvbnm");

    private PasswordPolicy() {
    }

    /** 규칙에 어긋나면 오류 문구, 모두 맞으면 null */
    public static String check(String password, String email) {
        String lower = password.toLowerCase(Locale.ROOT);

        if (lower.matches(".*(.)\\1\\1.*")) {
            return "같은 문자를 3번 이상 이어서 쓸 수 없습니다. (예: 111, aaa)";
        }
        if (hasSequence(lower)) {
            return "이어진 문자 4개는 쓸 수 없습니다. (예: 1234, abcd, qwer)";
        }
        String emailId = email == null ? "" : email.toLowerCase(Locale.ROOT).split("@")[0];
        if (emailId.length() >= 3 && lower.contains(emailId)) {
            return "비밀번호에 이메일 아이디를 넣을 수 없습니다.";
        }
        if (COMMON_WORDS.stream().anyMatch(lower::contains)) {
            return "너무 흔한 비밀번호입니다. 다른 비밀번호를 입력해 주세요.";
        }
        return null;
    }

    // 4글자씩 잘라 보면서, 순서대로든 거꾸로든 이어진 줄에 들어 있으면 true (예: 1234, 4321, abcd, qwer)
    private static boolean hasSequence(String lower) {
        for (int i = 0; i + 4 <= lower.length(); i++) {
            String part = lower.substring(i, i + 4);
            String reversed = new StringBuilder(part).reverse().toString();
            for (String line : SEQUENCES) {
                if (line.contains(part) || line.contains(reversed)) {
                    return true;
                }
            }
        }
        return false;
    }
}
