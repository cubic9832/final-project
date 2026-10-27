package com.kh.back.member.service;

import com.kh.back.member.dto.ProfileUpdateRequest;
import com.kh.back.member.dto.MemberResponse;
import com.kh.back.member.dto.UserAgreementDto;


public interface MemberService {

    // 회원 번호로 회원 정보를 찾는다 (비밀번호 제외)
    MemberResponse getMember(Long userId);

    // 닉네임 변경 (보완 3 추가). 다른 회원이 쓰는 닉네임이면 409 NICKNAME_DUPLICATED
    MemberResponse updateNickName(Long userId, String nickName);

    // 개인정보 수정 (6단계). 생년월일이 만 18세 미만이면 400 AGE_RESTRICTED (저장하지 않음)
    MemberResponse updateProfile(Long userId, ProfileUpdateRequest request);

    // 보완 9: 가입 동의 기록 · 이메일 알림 (V14 이전 회원은 기록 없음 · 알림 IMPORTANT)
    UserAgreementDto getAgreement(Long userId);

    // 보완 9: 이메일 알림 범위 바꾸기 (ALL 이면 추천 업데이트 수신 동의 시각을 남긴다)
    UserAgreementDto updateNotification(Long userId, String emailNotification);

    // 회원 탈퇴 (보완 4). 비밀번호가 맞으면 관련 데이터를 정리하고 회원을 삭제한다
    void withdraw(Long userId, String password, String confirmText);
}
