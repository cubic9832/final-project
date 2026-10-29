package com.kh.back.chatbot.dto;

import java.util.List;

public record ChatHistoryResponse(List<Message> messages, int remaining) {
    public record Message(String role, String text) {}
}
