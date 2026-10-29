package com.kh.back.chatbot.controller;

import com.kh.back.chatbot.dto.*;
import com.kh.back.chatbot.service.ChatService;
import com.kh.back.common.dto.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/chat-messages")
public class ChatController {
    private final ChatService service;

    @PostMapping
    public ApiResponse<ChatResponse> create(@Valid @RequestBody ChatRequest request) {
        return ApiResponse.ok(service.reply(request));
    }
}
