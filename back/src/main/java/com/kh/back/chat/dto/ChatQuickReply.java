package com.kh.back.chat.dto;

/**
 * 8단계: 상담원이 등록한 자주 쓰는 문구 1개 (chat_quick_reply).
 */
public record ChatQuickReply(Long id, String content) {
}
