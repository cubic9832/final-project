package com.kh.back.chat.controller;

import com.kh.back.chat.dto.ChatAdminOption;
import com.kh.back.chat.dto.ChatRoomDto;
import com.kh.back.chat.dto.ChatTransferRequest;
import com.kh.back.chat.service.ChatRoomService;
import com.kh.back.common.dto.ApiResponse;
import jakarta.validation.Valid;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 8단계: 1:1 상담 — 관리자 쪽 REST. /api/v1/admin/** 라서 SecurityConfig 가 관리자 · 총관리자만 통과시킨다 (일반 회원 404).
 * 넘기기 · 종료의 "담당자 또는 총관리자" 규칙은 ChatRoomServiceImpl 에서 본다.
 */
@RestController
@RequestMapping("/api/v1/admin/chat")
@RequiredArgsConstructor
public class AdminChatApiController {

    private final ChatRoomService chatRoomService;

    // GET /api/v1/admin/chat/rooms?status=WAITING — 상담 목록 (없으면 전체, 최근 메시지 순)
    // 호출: AdminChatPanel.jsx 화면이 열릴 때 · /topic/admin/chat 알림을 받을 때 → chatApi.getAdminRooms
    @GetMapping("/rooms")
    public ApiResponse<List<ChatRoomDto>> rooms(@RequestParam(required = false) String status) {
        return ApiResponse.ok(chatRoomService.getRooms(status));
    }

    // GET /api/v1/admin/chat/admins — 넘겨받을 수 있는 관리자 목록
    @GetMapping("/admins")
    public ApiResponse<List<ChatAdminOption>> admins() {
        return ApiResponse.ok(chatRoomService.getAdmins());
    }

    // POST /api/v1/admin/chat/rooms/{id}/assign — [맡기] (먼저 누른 관리자가 담당)
    @PostMapping("/rooms/{id}/assign")
    public ApiResponse<Void> assign(@AuthenticationPrincipal Long userId, @PathVariable Long id) {
        chatRoomService.assign(userId, id);
        return ApiResponse.ok(null);
    }

    // POST /api/v1/admin/chat/rooms/{id}/transfer — 본문 { adminId, reason } [넘기기]
    @PostMapping("/rooms/{id}/transfer")
    public ApiResponse<Void> transfer(@AuthenticationPrincipal Long userId, @PathVariable Long id,
                                      @Valid @RequestBody ChatTransferRequest request) {
        chatRoomService.transfer(userId, id, request.getAdminId(), request.getReason());
        return ApiResponse.ok(null);
    }

    // POST /api/v1/admin/chat/rooms/{id}/close — [상담 종료]
    @PostMapping("/rooms/{id}/close")
    public ApiResponse<Void> close(@AuthenticationPrincipal Long userId, @PathVariable Long id) {
        chatRoomService.closeByAdmin(userId, id);
        return ApiResponse.ok(null);
    }
}
