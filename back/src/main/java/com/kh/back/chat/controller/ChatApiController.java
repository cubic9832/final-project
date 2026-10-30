package com.kh.back.chat.controller;

import com.kh.back.chat.dto.ChatMessageDto;
import com.kh.back.chat.dto.ChatRoomDto;
import com.kh.back.chat.service.ChatRoomService;
import com.kh.back.common.dto.ApiResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 8단계: 1:1 상담 — 회원 쪽 REST (방 · 지난 메시지). 실시간 메시지는 ChatMessageController (STOMP).
 * 모두 로그인 필요 — SecurityConfig 의 anyRequest().authenticated() 에 걸린다.
 * 샘플 step4 와 달리 주소에 방 번호 대신 "me" — 회원은 자기 상담방 하나만 있다 (스터디 5 의 /members/me 와 같은 방식).
 */
@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor
public class ChatApiController {

    private final ChatRoomService chatRoomService;

    // GET /api/v1/chat/me — 내 상담방 (없으면 data: null)
    // 호출: ConsultationPage.jsx 화면이 열릴 때 · SYSTEM 메시지(연결 · 종료)를 받을 때 → chatApi.getMyRoom
    @GetMapping("/me")
    public ApiResponse<ChatRoomDto> myRoom(@AuthenticationPrincipal Long userId) {
        return ApiResponse.ok(chatRoomService.getMyRoom(userId));
    }

    // POST /api/v1/chat/me — [상담 시작] · [새로 상담하기] (처음이면 만들고, 종료됐으면 대기로)
    @PostMapping("/me")
    public ApiResponse<ChatRoomDto> start(@AuthenticationPrincipal Long userId) {
        return ApiResponse.ok(chatRoomService.startConsultation(userId));
    }

    // POST /api/v1/chat/me/close — 회원이 [상담 종료]
    @PostMapping("/me/close")
    public ApiResponse<Void> close(@AuthenticationPrincipal Long userId) {
        chatRoomService.closeByMember(userId);
        return ApiResponse.ok(null);
    }

    // GET /api/v1/chat/rooms/{roomId}/messages?beforeId=120&size=30 — beforeId 보다 오래된 메시지 30개 (샘플과 같음)
    // 회원은 내 방만, 관리자는 모든 방 (ChatRoomService.canView)
    @GetMapping("/rooms/{roomId}/messages")
    public ApiResponse<List<ChatMessageDto>> messages(@AuthenticationPrincipal Long userId,
                                                      @PathVariable Long roomId,
                                                      @RequestParam(required = false) Long beforeId,
                                                      @RequestParam(defaultValue = "30") int size) {
        size = Math.min(Math.max(size, 1), 100); // 한 번에 최대 100개
        return ApiResponse.ok(chatRoomService.getMessages(userId, roomId, beforeId, size));
    }
}
