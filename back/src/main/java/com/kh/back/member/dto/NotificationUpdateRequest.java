package com.kh.back.member.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// 보완 9: 이메일 알림 범위 바꾸기 (PUT /api/v1/members/me/notifications)
@Getter
@Setter
@NoArgsConstructor
public class NotificationUpdateRequest {

    @NotBlank(message = "알림 범위를 골라 주세요.")
    @Pattern(regexp = "^(ALL|IMPORTANT|NONE)$", message = "알림 범위를 다시 골라 주세요.")
    private String emailNotification;
}
