package com.kh.back.chatbot.dto;

import java.util.List;

public record ChatResponse(String answer, String question, int remaining, List<Source> sources) {
    public record Source(String id, String title, String content) {}
}
