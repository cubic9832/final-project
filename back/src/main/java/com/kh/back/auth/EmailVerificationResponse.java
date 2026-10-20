package com.kh.back.auth;

/**
 * [인증 코드 받기] 응답 (보완 7).
 * mailEnabled 가 false 면 개발 모드 — 메일 대신 서버 로그에 코드가 찍혔다는 뜻 (화면에 안내)
 * alreadyVerified(보완 7 추가): 30분 안에 이미 인증을 마친 이메일 → 메일을 보내지 않고 바로 인증 완료로
 */
public record EmailVerificationResponse(long expiresInSeconds, long resendAfterSeconds, boolean mailEnabled,
                                        boolean alreadyVerified) {
}
