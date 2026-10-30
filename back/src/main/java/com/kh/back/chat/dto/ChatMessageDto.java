package com.kh.back.chat.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

/**
 * 8단계: 메시지 chat_message 1행.
 * 보낸 사람 이름은 넣지 않는다 — 회원 화면은 ADMIN 을 "상담원", 관리자 화면은 USER 를 방의 회원 닉네임으로 그린다.
 */
@Getter
@Setter
@NoArgsConstructor
@ToString
public class ChatMessageDto {

    public static final String USER = "USER";
    public static final String ADMIN = "ADMIN";
    public static final String SYSTEM = "SYSTEM";

    private Long id;
    private Long roomId;
    private String senderType;
    private Long senderId;
    private String content;
    private LocalDateTime createdAt;
}
