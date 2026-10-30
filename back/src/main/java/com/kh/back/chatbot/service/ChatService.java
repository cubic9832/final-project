package com.kh.back.chatbot.service;

import com.kh.back.chatbot.dto.*;

public interface ChatService {
    ChatResponse reply(Long memberId, ChatRequest request);
    ChatResponse guideReply(Long memberId, ChatGuideRequest request);
    ChatHistoryResponse history(Long memberId);
    void clear(Long memberId);
}
