package com.kh.back.chatbot.service;

import com.kh.back.diagnosis.service.DiagnosisService;
import com.kh.back.taste.service.TasteService;
import com.kh.back.chatbot.util.PiiMasker;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class MemberUserContextProvider implements UserContextProvider {
    private final DiagnosisService diagnoses;
    private final TasteService tastes;
    @Override
    public String build(Long memberId) {
        var result = new StringBuilder();
        var recent = diagnoses.getRecent(memberId, 1);
        if (!recent.isEmpty()) {
            var diagnosis = recent.get(0);
            result.append("최근 저장된 진단 요약(현재 상황이나 확정 견적이 아님): 구매 전 월 여유금 ")
                    .append(diagnosis.getMonthlyAvailable()).append("원, 구매 가격 상한 ")
                    .append(diagnosis.getPriceUpper() == null ? "정보 없음" : diagnosis.getPriceUpper() + "원").append(".\n");
        }
        var current = tastes.current(memberId);
        if (current != null) {
            var type = tastes.catalog().types().get(current.primary());
            if (type != null) result.append("현재 저장된 자동차 취향: ").append(type.name()).append(".\n");
        }
        return result.isEmpty() ? "저장된 개인 결과 없음" : PiiMasker.mask(result.toString());
    }
}
