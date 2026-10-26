package com.kh.back.taste.service;

import com.kh.back.common.exception.ApiException;
import com.kh.back.taste.dto.CurrentTasteResponse;
import com.kh.back.taste.dto.TasteCatalogResponse;
import com.kh.back.taste.dto.TasteSaveRequest;
import com.kh.back.taste.repository.TasteRepository;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class TasteServiceTests {
    private TasteRepository repository;
    private TasteEvaluator evaluator;
    private TasteService service;
    private List<TasteSaveRequest.Answer> answers;

    @BeforeEach
    void setUp() {
        repository = mock(TasteRepository.class);
        evaluator = mock(TasteEvaluator.class);
        service = new TasteServiceImpl(repository, evaluator);
        answers = Collections.nCopies(8, new TasteSaveRequest.Answer("start", 1L));
    }

    @Test
    void missingMemberCannotWriteATaste() {
        assertThatThrownBy(() -> service.save(7L, new TasteSaveRequest(2, answers, null)))
                .isInstanceOfSatisfying(ApiException.class, error -> assertThat(error.getCode()).isEqualTo("MEMBER_NOT_FOUND"));
        verify(repository, never()).save(anyLong(), anyLong(), any());
        verifyNoInteractions(evaluator);
    }

    @Test
    void identicalPutKeepsPreviousSaveTimeAndDoesNotWriteAgain() {
        prepareCatalog();
        CurrentTasteResponse previous = storedTaste(answers);
        when(repository.find(7L)).thenReturn(previous);
        assertThat(service.save(7L, new TasteSaveRequest(2, answers, null))).isSameAs(previous);
        verify(repository, never()).save(anyLong(), anyLong(), any());
        verifyNoInteractions(evaluator);
    }

    @Test
    void staleVersionOrMissingReplacementTimestampCannotOverwriteTaste() {
        prepareCatalog();
        assertThatThrownBy(() -> service.save(7L, new TasteSaveRequest(1, answers, null)))
                .isInstanceOfSatisfying(ApiException.class, error -> assertThat(error.getCode()).isEqualTo("TASTE_VERSION_CHANGED"));
        when(repository.find(7L)).thenReturn(storedTaste(List.of()));
        assertThatThrownBy(() -> service.save(7L, new TasteSaveRequest(2, answers, null)))
                .isInstanceOfSatisfying(ApiException.class, error -> assertThat(error.getCode()).isEqualTo("TASTE_CHANGED"));
        verify(repository, never()).save(anyLong(), anyLong(), any());
    }

    @Test
    void firstSaveUsesAuthenticatedMemberAndServerCalculatedType() {
        prepareCatalog();
        CurrentTasteResponse saved = storedTaste(answers);
        when(repository.find(7L)).thenReturn(null, saved);
        when(evaluator.evaluate(any(), eq(answers))).thenReturn("city");
        assertThat(service.save(7L, new TasteSaveRequest(2, answers, null))).isEqualTo(saved);
        verify(repository).save(7L, 11L, answers);
    }

    private void prepareCatalog() {
        when(repository.lockMember(7L)).thenReturn(true);
        var type = new TasteCatalogResponse.Type(11L, "도심형", "", List.of(), List.of());
        when(repository.catalog()).thenReturn(new TasteCatalogResponse(1L, 2, 8, Map.of("city", type), List.of(), List.of()));
    }

    private CurrentTasteResponse storedTaste(List<TasteSaveRequest.Answer> savedAnswers) {
        return new CurrentTasteResponse(2, savedAnswers, "city", LocalDateTime.of(2026, 10, 26, 12, 0));
    }
}
