package com.kh.back.member.service;

import com.kh.back.member.dto.MemberResponse;

public interface MemberService {

    // 회원 번호로 회원 정보를 찾는다 (비밀번호 제외)
    MemberResponse getMember(Long userId);
}
