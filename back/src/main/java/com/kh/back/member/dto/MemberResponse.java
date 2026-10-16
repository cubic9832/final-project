package com.kh.back.member.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 화면에 내려보내는 회원 정보. 비밀번호(passwordHash)는 넣지 않는다.
 */
@Getter
@AllArgsConstructor
public class MemberResponse {

    private final Long id;
    private final String email;
    private final String nickName;
    private final String role;

    public static MemberResponse from(MemberDto member) {
        return new MemberResponse(member.getId(), member.getEmail(), member.getNickName(), member.getRole());
    }
}
