package com.kh.back.chatbot.service;

public interface UserContextProvider {
    String build(Long memberId);
}
