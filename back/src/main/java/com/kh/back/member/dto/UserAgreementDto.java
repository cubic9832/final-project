package com.kh.back.member.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.Setter;

/**
 * 보완 9: user_agreements 1행 (가입 동의 시각 · 이메일 알림 설정).
 * 화면 응답으로도 그대로 쓴다 (회원 번호 말고는 민감한 값이 없다).
 */
@Getter
@Setter
public class UserAgreementDto {

    public static final String DEFAULT_NOTIFICATION = "IMPORTANT";

    private Long userId;
    private LocalDateTime termsAgreedAt;
    private LocalDateTime privacyAgreedAt;
    private String emailNotification;   // ALL · IMPORTANT · NONE
    private LocalDateTime updatesAgreedAt;

    // 가입할 때: 필수 동의 2개는 지금 시각, [선택] 추천 업데이트에 동의했으면 알림 ALL + 동의 시각
    public static UserAgreementDto atSignup(Long userId, boolean updatesAgreed, LocalDateTime now) {
        UserAgreementDto agreement = new UserAgreementDto();
        agreement.setUserId(userId);
        agreement.setTermsAgreedAt(now);
        agreement.setPrivacyAgreedAt(now);
        agreement.setEmailNotification(updatesAgreed ? "ALL" : DEFAULT_NOTIFICATION);
        agreement.setUpdatesAgreedAt(updatesAgreed ? now : null);
        return agreement;
    }

    // 표가 생기기 전에 가입한 회원 (행 없음) → 동의 기록 없음 · 알림 기본값
    public static UserAgreementDto empty(Long userId) {
        UserAgreementDto agreement = new UserAgreementDto();
        agreement.setUserId(userId);
        agreement.setEmailNotification(DEFAULT_NOTIFICATION);
        return agreement;
    }
}
