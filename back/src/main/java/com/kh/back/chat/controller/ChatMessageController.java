package com.kh.back.chat.controller;

import com.kh.back.chat.dto.ChatSendRequest;
import com.kh.back.chat.service.ChatRoomService;
import com.kh.back.common.dto.ApiResponse;
import com.kh.back.common.exception.ApiException;
import java.security.Principal;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageExceptionHandler;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.simp.annotation.SendToUser;
import org.springframework.stereotype.Controller;

/**
 * 8단계: 실시간 메시지 (STOMP). 샘플 step4 의 ChatMessageController 와 같은 구조.
 * @RestController 가 아니다 — 응답은 return 이 아니라 ChatBroadcaster 가 구독 주소로 보낸다.
 */
@Controller
@RequiredArgsConstructor
public class ChatMessageController {

    private final ChatRoomService chatRoomService;

    // 화면이 SEND /app/chat/rooms/1 → 이 메서드 (/app 은 빼고 적는다)
    // 저장 → /topic/chat/rooms/1 구독자(회원 · 관리자) 전원에게 보내기는 ChatRoomServiceImpl.sendMessage 가 한다
    @MessageMapping("/chat/rooms/{roomId}")
    public void send(@DestinationVariable Long roomId, @Payload ChatSendRequest request, Principal principal) {
        Long userId = Long.valueOf(principal.getName()); // CONNECT 때 StompAuthInterceptor 가 기록한 회원 번호
        chatRoomService.sendMessage(userId, roomId, request.getContent());
    }

    // send() 에서 ApiException 이 나면 → 보낸 사람에게만 /user/queue/errors 로 알린다. 연결은 유지된다
    @MessageExceptionHandler(ApiException.class)
    @SendToUser("/queue/errors")
    public ApiResponse<Void> handleError(ApiException e) {
        return ApiResponse.fail(e.getCode(), e.getMessage());
    }
}
