package com.kh.back.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 8단계: 자주 쓰는 문구 등록 { "content": "확인 후 바로 안내해 드리겠습니다." }.
 */
@Getter
@Setter
@NoArgsConstructor
public class ChatQuickReplyRequest {

    @NotBlank(message = "문구를 입력해 주세요.")
    @Size(max = 200, message = "문구는 200자까지 쓸 수 있습니다.")
    private String content;
}
