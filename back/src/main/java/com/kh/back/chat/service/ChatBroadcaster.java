package com.kh.back.chat.service;

import com.kh.back.chat.dto.ChatMessageDto;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

/**
 * 8단계: 서버 → 화면 실시간 알림 (STOMP 구독 주소로 보낸다).
 *   /topic/chat/rooms/{id} : 그 상담방의 새 메시지 (회원 · 관리자 화면이 구독)
 *   /topic/admin/chat      : 상담 목록이 바뀜 (새 상담 · 맡기 · 넘기기 · 종료 · 새 메시지) → 관리자 화면이 목록을 다시 불러온다
 * Service 가 SimpMessagingTemplate 을 직접 쓰지 않고 여기를 거친다 → 테스트에서 이 클래스만 가짜로 바꾸면 된다
 */
@Component
@RequiredArgsConstructor
public class ChatBroadcaster {

    static final String ROOM_TOPIC = "/topic/chat/rooms/";
    static final String ADMIN_TOPIC = "/topic/admin/chat";

    private final SimpMessagingTemplate messagingTemplate;

    public void message(ChatMessageDto message) {
        messagingTemplate.convertAndSend(ROOM_TOPIC + message.getRoomId(), message);
    }

    // 목록 화면은 무엇이 바뀌었는지만 알면 된다 (자세한 내용은 REST 로 다시 읽는다 — 권한 검사를 한 곳에서)
    public void roomChanged(Long roomId, String status) {
        Object payload = Map.of("roomId", roomId, "status", status); // Object 로 받아야 "헤더 Map" 으로 오해하지 않는다
        messagingTemplate.convertAndSend(ADMIN_TOPIC, payload);
    }
}
