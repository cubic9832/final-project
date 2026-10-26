package com.kh.back.auth.service;

import java.util.List;
import java.util.Locale;

/**
 * 닉네임 금지어 (보완 3 추가 · 10-20).
 * 길이(2~12자)는 SignupRequest · NickNameUpdateRequest 의 @Size 가 먼저 검사하고, 여기서는 들어가면 안 되는 단어를 본다.
 * 프론트 front/src/features/auth/nickNamePolicy.js 와 같은 목록을 쓴다.
 * 회원가입 · 구글 가입 · 마이페이지 닉네임 변경 · [중복 확인] 모두 이 검사를 거친다. 이미 가입한 회원의 닉네임은 그대로 둔다.
 */
public final class NickNamePolicy {

    // 운영자로 오해될 수 있는 단어 (사칭 방지)
    private static final List<String> RESERVED_WORDS = List.of(
            "admin", "root", "system", "operator", "staff", "official", "creditcompass",
            "관리자", "운영자", "운영진", "운영팀", "고객센터", "시스템", "크레딧컴퍼스", "크레딧컴패스", "공식계정");

    // 욕설 · 비속어 (대표적인 것만. 변형까지 모두 막을 수는 없다)
    private static final List<String> BAD_WORDS = List.of(
            "시발", "씨발", "씨바", "ㅅㅂ", "병신", "븅신", "ㅂㅅ", "ㅄ", "좆", "존나", "새끼", "지랄",
            "미친놈", "미친년", "애미", "느금", "섹스", "fuck", "shit", "bitch", "sex");

    private NickNamePolicy() {
    }

    /** 금지어가 들어 있으면 오류 문구, 없으면 null */
    public static String check(String nickName) {
        String normalized = normalize(nickName);
        if (RESERVED_WORDS.stream().anyMatch(normalized::contains)) {
            return "운영자로 오해할 수 있는 닉네임은 쓸 수 없습니다.";
        }
        if (BAD_WORDS.stream().anyMatch(normalized::contains)) {
            return "사용할 수 없는 단어가 들어 있습니다.";
        }
        return null;
    }

    // 소문자로 바꾸고 공백 · 숫자 · 기호를 지운다 → "관 리 자", "Admin_01", "시1발" 도 걸린다
    private static String normalize(String nickName) {
        String lower = nickName == null ? "" : nickName.toLowerCase(Locale.ROOT);
        return lower.replaceAll("[\\s\\d\\p{Punct}]", "");
    }
}
