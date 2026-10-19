package com.kh.back.member.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 회원 탈퇴 요청 본문 (보완 4). 되돌릴 수 없는 작업이라 비밀번호를 한 번 더 확인한다.
 */
@Getter
@Setter
@NoArgsConstructor
public class WithdrawRequest {

    @NotBlank(message = "비밀번호를 입력해 주세요.")
    private String password;
}
