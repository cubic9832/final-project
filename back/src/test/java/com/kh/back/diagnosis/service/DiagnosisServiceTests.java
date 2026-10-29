package com.kh.back.diagnosis.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.common.exception.ApiException;
import com.kh.back.diagnosis.dto.DiagnosisRow;
import com.kh.back.diagnosis.dto.DiagnosisSaveRequest;
import com.kh.back.diagnosis.dto.DiagnosisSummary;
import com.kh.back.diagnosis.mapper.DiagnosisMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

// 재무 진단 기록: 표 3개에 순서대로 저장, 처음 보는 모델 버전은 등록, 로그인 안 하면 저장 안 함
@ExtendWith(MockitoExtension.class)
class DiagnosisServiceTests {

    @Mock DiagnosisMapper diagnosisMapper;
    @InjectMocks DiagnosisServiceImpl diagnosisService;

    private DiagnosisSaveRequest request() {
        DiagnosisSaveRequest request = new DiagnosisSaveRequest();
        request.setModelVersion("candidate-v2");
        request.setMonthlyIncome(3_000_000L);
        request.setMonthlyExpense(1_800_000L);
        request.setMonthlyAvailable(1_200_000L);
        request.setPurchaseFunds(20_000_000L);
        request.setPriceUpper(25_000_000L);
        return request;
    }

    @Test
    void 입력_버전_소득_결과_순서로_저장한다() {
        when(diagnosisMapper.findModelVersionId(DiagnosisServiceImpl.MODEL_NAME, "candidate-v2")).thenReturn(4L);
        doAnswer(inv -> { ((DiagnosisRow) inv.getArgument(0)).setAnalysisId(77L); return null; })
                .when(diagnosisMapper).insertAnalysisRun(any());

        DiagnosisSummary saved = diagnosisService.save(9L, request());

        InOrder order = inOrder(diagnosisMapper);
        order.verify(diagnosisMapper).insertSnapshot(any());
        order.verify(diagnosisMapper).insertFinancialProfile(any());
        order.verify(diagnosisMapper).insertAnalysisRun(any());
        verify(diagnosisMapper, never()).insertModelVersion(anyString(), anyString());
        assertThat(saved.getAnalysisId()).isEqualTo(77L);
        assertThat(saved.getMonthlyAvailable()).isEqualTo(1_200_000L);
    }

    @Test
    void 처음_보는_모델_버전은_등록한다() {
        when(diagnosisMapper.findModelVersionId(DiagnosisServiceImpl.MODEL_NAME, "candidate-v2")).thenReturn(null, 5L);

        diagnosisService.save(9L, request());

        verify(diagnosisMapper).insertModelVersion(DiagnosisServiceImpl.MODEL_NAME, "candidate-v2");
    }

    @Test
    void 로그인하지_않으면_저장하지_않는다() {
        assertThatThrownBy(() -> diagnosisService.save(null, request()))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("AUTH_REQUIRED"));
        verify(diagnosisMapper, never()).insertSnapshot(any());
    }
}
