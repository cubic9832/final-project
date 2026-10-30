package com.kh.back.chat.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

/**
 * 8단계: 상담방 chat_room 1행 + 회원 · 담당 관리자 닉네임 (ChatMapper.xml 에서 users 와 JOIN).
 * 회원 화면에는 담당 관리자 닉네임을 보내지 않는다 (상담원으로만 표시 — ChatRoomService.getMyRoom 이 지운다).
 */
@Getter
@Setter
@NoArgsConstructor
@ToString
public class ChatRoomDto {

    public static final String WAITING = "WAITING";
    public static final String ACTIVE = "ACTIVE";
    public static final String CLOSED = "CLOSED";

    private Long id;
    private Long userId;
    private String userNickName;
    private String status;
    private Long assignedAdminId;
    private String assignedAdminNickName;
    private String lastMessage;        // 관리자 목록의 미리보기 (마지막 메시지 앞부분)
    private LocalDateTime lastMessageAt;
    private LocalDateTime createdAt;
    private LocalDateTime restrictedUntil; // 상담 제한이 끝나는 시각 (제한한 적 없으면 null)
    private boolean restricted;            // 지금 제한 중인가 (DB 시각 기준으로 SQL 에서 계산)
}
