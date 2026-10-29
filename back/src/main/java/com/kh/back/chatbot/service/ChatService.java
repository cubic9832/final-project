package com.kh.back.chatbot.service;

import com.kh.back.chatbot.dto.*;
import com.kh.back.common.exception.ApiException;
import java.util.List;
import java.util.concurrent.Semaphore;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ChatService {
    private final ChatKnowledge knowledge;
    private final GeminiClient gemini;
    private final Semaphore capacity = new Semaphore(4);

    public ChatResponse reply(ChatRequest request) {
        List<ChatRequest.Turn> history = request.history() == null ? List.of() : request.history();
        for (int i = 0; i < history.size(); i++) {
            if (!history.get(i).role().equals(i % 2 == 0 ? "user" : "model")) throw invalidHistory();
        }
        if (history.size() % 2 != 0) throw invalidHistory();
        if (!capacity.tryAcquire()) throw new ApiException(HttpStatus.TOO_MANY_REQUESTS,
                "CHAT_BUSY", "현재 상담 요청이 많습니다. 잠시 후 다시 시도해 주세요.");
        try {
            // Include the last question to retrieve context for short follow-up questions too.
            String query = (history.isEmpty() ? "" : history.get(history.size() - 2).text() + " ") + request.message();
            var context = knowledge.search(query);
            String answer = gemini.generate(request.message(), history, context);
            return new ChatResponse(answer, context.stream()
                    .map(chunk -> new ChatResponse.Source(chunk.id(), chunk.title(), chunk.text())).toList());
        } finally {
            capacity.release();
        }
    }

    private ApiException invalidHistory() {
        return new ApiException(HttpStatus.BAD_REQUEST, "CHAT_INVALID_HISTORY", "대화 기록 형식이 올바르지 않습니다.");
    }
}
