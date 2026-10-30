package com.kh.back.chat.dto;

/**
 * 8단계: 상담을 넘겨받을 수 있는 관리자 (넘기기 선택 목록).
 */
public record ChatAdminOption(Long id, String nickName, String role) {
}
