package com.kh.back.chat.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 8단계: 상담 제한 { "days": 3, "reason": "욕설 · 비속어" }. 이 기간 동안 회원은 새 상담을 시작할 수 없다.
 * days = 0 이면 영구 (총관리자만). 이유는 운영 로그에만 남긴다.
 */
@Getter
@Setter
@NoArgsConstructor
public class ChatRestrictRequest {

    public static final int PERMANENT = 0;

    @NotNull(message = "제한 기간을 골라 주세요.")
    @Min(value = 0, message = "제한 기간은 1~30일 또는 영구입니다.")
    @Max(value = 30, message = "제한 기간은 1~30일 또는 영구입니다.")
    private Integer days;

    @Size(max = 100, message = "이유는 100자까지 쓸 수 있습니다.")
    private String reason;
}
