package com.kh.back.admin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// 7단계: 총관리자가 회원 권한을 바꾸는 요청 — 관리자로 지정(ADMIN) 또는 해제(USER) 만. 총관리자 지정은 DB 에서만
@Getter
@Setter
@NoArgsConstructor
public class RoleChangeRequest {

    @NotBlank(message = "바꿀 권한을 골라 주세요.")
    @Pattern(regexp = "^(USER|ADMIN)$", message = "관리자로 지정하거나 해제만 할 수 있습니다.")
    private String role;
}
