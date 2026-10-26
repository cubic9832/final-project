package com.kh.back.auth.dto;

/**
 * [인증 코드 받기] 응답 (보완 7).
 * mailEnabled 가 false 면 개발 모드 — 메일 대신 서버 로그에 코드가 찍혔다는 뜻 (화면에 안내)
 * (10-22: "이미 인증됨" 응답은 없앴다 — 새로고침 뒤에는 화면이 보관한 일회용 증명 번호로 이어서 진행)
 */
public record EmailVerificationResponse(long expiresInSeconds, long resendAfterSeconds, boolean mailEnabled) {
}
