package com.kh.back.member;

import java.time.LocalDate;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 화면에 내려보내는 회원 정보. 비밀번호(passwordHash)는 넣지 않는다.
 * 보완 5: 개인 정보는 user_profiles 에서 가져오고, 전화번호는 가운데를 가려서 보낸다 (예: 010-****-5678).
 * 보완 5 이전에 가입한 회원은 개인 정보가 없어 null 이다.
 */
@Getter
@AllArgsConstructor
public class MemberResponse {

    private final Long id;
    private final String email;
    private final String nickName;
    private final String role;
    private final String phoneMasked;
    private final LocalDate birthDate;
    private final String gender;
    private final boolean socialOnly; // 보완 8: 구글로만 가입 (탈퇴 때 비밀번호 대신 "탈퇴" 입력)

    public static MemberResponse from(MemberDto member) {
        return from(member, null);
    }

    public static MemberResponse from(MemberDto member, UserProfileDto profile) {
        return new MemberResponse(
                member.getId(), member.getEmail(), member.getNickName(), member.getRole(),
                profile == null ? null : maskPhone(profile.getPhone()),
                profile == null ? null : profile.getBirthDate(),
                profile == null ? null : profile.getGender(),
                member.isSocialOnly());
    }

    // 01012345678 → 010-****-5678 (응답에 전체 번호를 싣지 않는다)
    private static String maskPhone(String phone) {
        if (phone == null || phone.length() != 11) {
            return null;
        }
        return phone.substring(0, 3) + "-****-" + phone.substring(7);
    }
}
