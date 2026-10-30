package com.kh.back.chatbot.service;

import com.kh.back.chatbot.dto.ChatRequest;
import com.kh.back.common.exception.ApiException;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.*;

@Component
@Slf4j
public class GeminiClient {
    private final String apiKey;
    private final String model;
    private final RestClient client;

    @Autowired
    public GeminiClient(@Value("${chatbot.gemini.api-key:}") String apiKey,
                        @Value("${chatbot.gemini.model:gemini-3.5-flash-lite}") String model) {
        this(apiKey, model, createClient());
    }

    GeminiClient(String apiKey, String model, RestClient client) {
        this.apiKey = apiKey;
        this.model = model;
        this.client = client;
    }

    private static RestClient createClient() {
        var factory = new JdkClientHttpRequestFactory(HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10)).build());
        factory.setReadTimeout(Duration.ofSeconds(30));
        return RestClient.builder().baseUrl("https://generativelanguage.googleapis.com/v1beta")
                .requestFactory(factory).build();
    }

    public boolean enabled() { return !apiKey.isBlank(); }

    public String generate(String question, List<ChatRequest.Turn> history, String instruction) {
        if (apiKey.isBlank()) throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE,
                "CHAT_NOT_CONFIGURED", "챗봇 연결을 준비 중입니다. 잠시 후 다시 이용해 주세요.");
        var contents = new ArrayList<Map<String, Object>>();
        for (var turn : history) contents.add(content(turn.role(), turn.text()));
        contents.add(content("user", question));
        try {
            Map<?, ?> response = client.post().uri("/models/{model}:generateContent", model)
                    .header("x-goog-api-key", apiKey).contentType(MediaType.APPLICATION_JSON)
                    .body(Map.of("systemInstruction", Map.of("parts", List.of(Map.of("text", instruction))),
                            "contents", contents, "generationConfig", Map.of("maxOutputTokens", 2048)))
                    .retrieve().body(Map.class);
            String answer = extractAnswer(response);
            if (answer.isBlank()) throw new ApiException(HttpStatus.BAD_GATEWAY, "CHAT_EMPTY_RESPONSE",
                    "답변을 만들지 못했습니다. 질문을 바꿔 다시 시도해 주세요.");
            return answer;
        } catch (RestClientResponseException error) {
            log.warn("Gemini request rejected: model={}, status={}", model, error.getStatusCode().value());
            if (error.getStatusCode().value() == 429) throw new ApiException(HttpStatus.TOO_MANY_REQUESTS,
                    "CHAT_RATE_LIMITED", "챗봇 사용량이 초과되었습니다. 잠시 후 다시 시도해 주세요.");
            if (error.getStatusCode().value() == 404) throw new ApiException(HttpStatus.BAD_GATEWAY,
                    "CHAT_MODEL_UNAVAILABLE", "설정된 Gemini 모델을 사용할 수 없습니다. 서버의 GEMINI_MODEL 설정을 확인해 주세요.");
            if (error.getStatusCode().value() == 401 || error.getStatusCode().value() == 403) {
                throw new ApiException(HttpStatus.BAD_GATEWAY, "CHAT_KEY_REJECTED",
                        "Gemini API 키 또는 프로젝트 권한을 확인해 주세요.");
            }
            throw new ApiException(HttpStatus.BAD_GATEWAY, "CHAT_PROVIDER_ERROR", "챗봇 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.");
        } catch (ResourceAccessException error) {
            log.warn("Gemini transport failed: model={}, cause={}", model,
                    error.getMostSpecificCause().getClass().getSimpleName());
            throw new ApiException(HttpStatus.GATEWAY_TIMEOUT, "CHAT_TIMEOUT", "답변이 지연되고 있습니다. 다시 시도해 주세요.");
        } catch (RestClientException error) {
            throw new ApiException(HttpStatus.BAD_GATEWAY, "CHAT_PROVIDER_ERROR", "챗봇 응답을 읽지 못했습니다. 다시 시도해 주세요.");
        }
    }

    private Map<String, Object> content(String role, String text) {
        return Map.of("role", role, "parts", List.of(Map.of("text", text)));
    }

    static String extractAnswer(Map<?, ?> response) {
        if (response == null || !(response.get("candidates") instanceof List<?> candidates) || candidates.isEmpty()) return "";
        if (!(candidates.get(0) instanceof Map<?, ?> candidate)
                || !(candidate.get("content") instanceof Map<?, ?> content)
                || !(content.get("parts") instanceof List<?> parts)) return "";
        return parts.stream().filter(part -> part instanceof Map<?, ?>)
                .map(part -> (Map<?, ?>) part).filter(part -> !Boolean.TRUE.equals(part.get("thought")))
                .map(part -> part.get("text")).filter(text -> text instanceof String)
                .map(Object::toString).collect(Collectors.joining("\n")).trim();
    }
}
