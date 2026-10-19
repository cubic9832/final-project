package com.kh.back.member;

import com.kh.back.member.MemberResponse;

public interface MemberService {

    // 회원 번호로 회원 정보를 찾는다 (비밀번호 제외)
    MemberResponse getMember(Long userId);

    // 회원 탈퇴 (보완 4). 비밀번호가 맞으면 관련 데이터를 정리하고 회원을 삭제한다
    void withdraw(Long userId, String password);
}
