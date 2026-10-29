package com.kh.back.chatbot.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;

@Component
public class ChatPrompt {
    private final String template;
    public ChatPrompt(@Value("classpath:prompts/chatbot-system.st") Resource resource) throws IOException {
        template = resource.getContentAsString(StandardCharsets.UTF_8);
    }
    public String build(String personal, List<ChatKnowledge.Chunk> context) {
        String documents = context.stream().map(chunk -> chunk.title() + "\n" + chunk.text()).collect(Collectors.joining("\n\n"));
        return template + "\n[사용자 정보]\n" + personal + "\n\n[검색 자료]\n" + documents;
    }
}
