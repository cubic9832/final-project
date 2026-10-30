package com.kh.back.chat.dto;

import java.math.BigDecimal;

/**
 * 8단계: 상담원별 만족도 — 평가 수 · 평균(소수 1자리) · 신고 수. 총관리자만 본다.
 */
public record ChatFeedbackSummary(Long adminId, String nickName, Long count, BigDecimal averageRating, Long reportCount) {
}
