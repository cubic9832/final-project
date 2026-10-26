package com.kh.back.taste.service;

import com.kh.back.taste.dto.CurrentTasteResponse;
import com.kh.back.taste.dto.TasteCatalogResponse;
import com.kh.back.taste.dto.TasteSaveRequest;
import com.kh.back.taste.repository.TasteRepository;

import com.kh.back.common.exception.ApiException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class TasteServiceImpl implements TasteService {
    private final TasteRepository repository;
    private final TasteEvaluator evaluator;

    @Override
    @Transactional(readOnly = true)
    public TasteCatalogResponse catalog() {
        return repository.catalog();
    }

    @Override
    @Transactional(readOnly = true)
    public CurrentTasteResponse current(long userId) {
        return repository.find(userId);
    }

    @Override
    @Transactional
    public CurrentTasteResponse save(long userId, TasteSaveRequest request) {
        if (!repository.lockMember(userId)) throw new ApiException(HttpStatus.UNAUTHORIZED,"MEMBER_NOT_FOUND","회원 정보를 확인해 주세요.");
        var catalog = repository.catalog();
        if (request.version() != catalog.version()) throw new ApiException(HttpStatus.CONFLICT,"TASTE_VERSION_CHANGED","질문이 변경됐습니다. 테스트를 새로 시작해 주세요.");
        var previous = repository.find(userId);
        // 동일한 PUT 재전송은 저장 시각도 바꾸지 않는다.
        if (previous != null && previous.version() == request.version() && previous.answers().equals(request.answers())) return previous;
        java.time.LocalDateTime expected;
        try {
            expected = request.expectedSavedAt() == null ? null : java.time.LocalDateTime.parse(request.expectedSavedAt());
        } catch (java.time.format.DateTimeParseException error) {
            throw new ApiException(HttpStatus.BAD_REQUEST,"INVALID_TASTE_TIMESTAMP","저장한 취향의 시각을 확인해 주세요.");
        }
        if (!java.util.Objects.equals(previous == null ? null : previous.savedAt(), expected))
            throw new ApiException(HttpStatus.CONFLICT,"TASTE_CHANGED","다른 화면에서 취향이 변경됐습니다. 새로고침 후 다시 확인해 주세요.");
        String primary = evaluator.evaluate(catalog, request.answers());
        repository.save(userId,catalog.types().get(primary).id(),request.answers());
        return repository.find(userId);
    }
}
