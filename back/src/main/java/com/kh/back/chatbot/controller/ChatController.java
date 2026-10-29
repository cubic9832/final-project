package com.kh.back.chatbot.controller;

import com.kh.back.chatbot.dto.*;
import com.kh.back.chatbot.service.ChatService;
import com.kh.back.common.dto.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.security.core.annotation.AuthenticationPrincipal;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/chat-messages")
public class ChatController {
    private final ChatService service;

    @PostMapping
    public ApiResponse<ChatResponse> create(@AuthenticationPrincipal Long memberId, @Valid @RequestBody ChatRequest request) {
        return ApiResponse.ok(service.reply(memberId, request));
    }

    @PostMapping("/guides")
    public ApiResponse<ChatResponse> guide(@AuthenticationPrincipal Long memberId, @Valid @RequestBody ChatGuideRequest request) {
        return ApiResponse.ok(service.guideReply(memberId, request));
    }

    @GetMapping
    public ApiResponse<ChatHistoryResponse> history(@AuthenticationPrincipal Long memberId) {
        return ApiResponse.ok(service.history(memberId));
    }

    @DeleteMapping
    public ApiResponse<Void> clear(@AuthenticationPrincipal Long memberId) {
        service.clear(memberId);
        return ApiResponse.ok(null);
    }
}
