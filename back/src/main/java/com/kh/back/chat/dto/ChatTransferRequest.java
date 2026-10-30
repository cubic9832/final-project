package com.kh.back.chat.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 8단계: 상담 넘기기 { "adminId": 3, "reason": "휴가" }. 이유는 선택, 운영 로그에만 남긴다 (회원에게는 "상담원이 바뀌었습니다" 만).
 */
@Getter
@Setter
@NoArgsConstructor
public class ChatTransferRequest {

    @NotNull(message = "넘겨받을 관리자를 골라 주세요.")
    private Long adminId;

    @Size(max = 100, message = "이유는 100자까지 쓸 수 있습니다.")
    private String reason;
}
