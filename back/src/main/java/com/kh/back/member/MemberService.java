package com.kh.back.member;


public interface MemberService {

    // 회원 번호로 회원 정보를 찾는다 (비밀번호 제외)
    MemberResponse getMember(Long userId);

    // 닉네임 변경 (보완 3 추가). 다른 회원이 쓰는 닉네임이면 409 NICKNAME_DUPLICATED
    MemberResponse updateNickName(Long userId, String nickName);

    // 회원 탈퇴 (보완 4). 비밀번호가 맞으면 관련 데이터를 정리하고 회원을 삭제한다
    void withdraw(Long userId, String password);
}
