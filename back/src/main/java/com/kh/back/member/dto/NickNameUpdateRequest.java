package com.kh.back.member.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 닉네임 변경 요청 본문 (보완 3 추가). 회원가입과 같은 2~12자 규칙.
 */
@Getter
@Setter
@NoArgsConstructor
public class NickNameUpdateRequest {

    @NotBlank(message = "이름 또는 닉네임을 입력해 주세요.")
    @Size(min = 2, max = 12, message = "이름 또는 닉네임은 2~12자로 입력해 주세요.")
    private String nickName;

    // 회원가입과 같은 규칙: 앞뒤 공백을 먼저 지운다
    public void setNickName(String nickName) {
        this.nickName = nickName == null ? null : nickName.trim();
    }
}
