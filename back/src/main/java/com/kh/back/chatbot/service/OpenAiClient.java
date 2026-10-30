package com.kh.back.chatbot.service;

import com.kh.back.common.exception.ApiException;
import java.util.List;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.Message;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import lombok.extern.slf4j.Slf4j;

@Component
@Slf4j
public class OpenAiClient {
    private final ChatClient client;
    private final boolean enabled;
    public OpenAiClient(ChatClient.Builder builder, @Value("${spring.ai.openai.api-key:no-key}") String key) {
        client = builder.build();
        enabled = !key.isBlank() && !"no-key".equals(key);
    }
    public boolean enabled() { return enabled; }
    public String generate(String instruction, String question, List<Message> history) {
        if (!enabled) throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "CHAT_NOT_CONFIGURED", "OpenAI API 키가 설정되지 않았습니다.");
        try {
            String answer = client.prompt().system(instruction).messages(history).user(question).call().content();
            if (answer == null || answer.isBlank()) throw new ApiException(HttpStatus.BAD_GATEWAY, "CHAT_EMPTY_RESPONSE", "답변을 만들지 못했습니다. 잠시 후 다시 시도해 주세요.");
            return answer;
        } catch (ApiException error) { throw error;
        } catch (RuntimeException error) {
            log.warn("OpenAI request failed: cause={}", error.getClass().getSimpleName());
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "CHAT_PROVIDER_ERROR", "챗봇 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.");
        }
    }
}
