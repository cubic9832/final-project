package com.kh.back.taste.service;

import com.kh.back.taste.dto.TasteCatalogResponse;
import com.kh.back.taste.dto.TasteSaveRequest;

import com.kh.back.common.exception.ApiException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

/** 클라이언트 결과를 신뢰하지 않고 공개 중인 DB 규칙으로 8개 답변을 검증한다. */
@Component
public class TasteEvaluator {
    public String evaluate(TasteCatalogResponse catalog, List<TasteSaveRequest.Answer> answers) {
        if (answers == null || answers.size() != catalog.questionCount()) throw invalid();
        Map<String, Integer> scores = new LinkedHashMap<>();
        catalog.types().keySet().forEach(key -> scores.put(key, 0));
        TasteCatalogResponse.Question question = catalog.questions().stream().filter(q -> q.initial() && q.step() == 1).findFirst().orElseThrow();
        for (int step = 0; step < answers.size(); step++) {
            var answer = answers.get(step);
            if (answer == null || question.step() != step + 1 || !question.id().equals(answer.questionId())) throw invalid();
            var option = question.options().stream().filter(o -> Long.valueOf(o.id()).equals(answer.optionId())).findFirst().orElseThrow(TasteEvaluator::invalid);
            option.weights().forEach((key, weight) -> scores.compute(key, (k, previous) -> previous + weight));
            if (step == answers.size() - 1) break;
            String source = question.id();
            String winner = leadingType(scores);
            var branch = catalog.rules().stream().filter(r -> r.sourceId().equals(source)
                    && (r.optionId() == null || r.optionId() == option.id())
                    && (r.leadingType() == null || r.leadingType().equals(winner))).findFirst().orElseThrow(TasteEvaluator::invalid);
            question = catalog.questions().stream().filter(q -> q.id().equals(branch.nextId())).findFirst().orElseThrow(TasteEvaluator::invalid);
        }
        return leadingType(scores);
    }

    private static String leadingType(Map<String, Integer> scores) {
        return scores.entrySet().stream().max(Map.Entry.comparingByValue()).orElseThrow().getKey();
    }

    private static ApiException invalid() {
        return new ApiException(HttpStatus.BAD_REQUEST, "INVALID_TASTE_ANSWERS", "8개 질문과 선택한 분기를 확인해 주세요.");
    }
}
