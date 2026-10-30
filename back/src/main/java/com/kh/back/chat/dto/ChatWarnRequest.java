package com.kh.back.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 8단계: 상담원 경고 { "reason": "욕설 · 비속어" }. 사유는 회원에게도 안내된다 (무엇이 문제인지 알려야 고칠 수 있다).
 */
@Getter
@Setter
@NoArgsConstructor
public class ChatWarnRequest {

    @NotBlank(message = "경고 사유를 골라 주세요.")
    @Size(max = 100, message = "사유는 100자까지 쓸 수 있습니다.")
    private String reason;
}
