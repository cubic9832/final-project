package com.kh.back.auth.dto;

/**
 * 인증 코드 확인 응답 (보완 7 추가 · 10-22): 일회용 증명 번호.
 * 화면은 이 번호를 회원가입 · 비밀번호 재설정 요청에 같이 보낸다 (없거나 다른 사람 것이면 400 EMAIL_NOT_VERIFIED)
 */
public record EmailVerificationProof(String verificationToken) {
}
