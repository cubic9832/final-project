package com.kh.back.diagnosis.service;

import com.kh.back.common.exception.ApiException;
import com.kh.back.diagnosis.dto.DiagnosisRow;
import com.kh.back.diagnosis.dto.DiagnosisSaveRequest;
import com.kh.back.diagnosis.dto.DiagnosisSummary;
import com.kh.back.diagnosis.mapper.DiagnosisMapper;
import java.time.LocalDateTime;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class DiagnosisServiceImpl implements DiagnosisService {

    // model_versions 에 남길 추천 서버 이름 (버전은 추천 서버 응답의 modelVersion, 예: candidate-v2)
    static final String MODEL_NAME = "vehicle-candidate-recommender";

    private final DiagnosisMapper diagnosisMapper;

    // 표 3개(입력 버전 → 소득 · 지출 · 예금 → 분석 결과)를 한 트랜잭션으로 → 중간에 실패하면 반쪽 기록이 남지 않는다
    @Override
    @Transactional
    public DiagnosisSummary save(Long userId, DiagnosisSaveRequest request) {
        if (userId == null) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "AUTH_REQUIRED", "로그인이 필요합니다.");
        }
        DiagnosisRow row = new DiagnosisRow();
        row.setUserId(userId);
        row.setModelVersionId(modelVersionId(request.getModelVersion()));
        row.setMonthlyIncome(request.getMonthlyIncome());
        row.setMonthlyExpense(request.getMonthlyExpense());
        row.setMonthlyAvailable(request.getMonthlyAvailable());
        row.setPurchaseFunds(request.getPurchaseFunds());
        row.setPriceUpper(request.getPriceUpper());

        diagnosisMapper.insertSnapshot(row);          // snapshotId 가 채워진다
        diagnosisMapper.insertFinancialProfile(row);
        diagnosisMapper.insertAnalysisRun(row);       // analysisId 가 채워진다

        DiagnosisSummary saved = new DiagnosisSummary();
        saved.setAnalysisId(row.getAnalysisId());
        saved.setCompletedAt(LocalDateTime.now());
        saved.setMonthlyIncome(row.getMonthlyIncome());
        saved.setMonthlyAvailable(row.getMonthlyAvailable());
        saved.setPurchaseFunds(row.getPurchaseFunds());
        saved.setPriceUpper(row.getPriceUpper());
        return saved;
    }

    @Override
    @Transactional(readOnly = true)
    public List<DiagnosisSummary> getRecent(Long userId, int size) {
        return diagnosisMapper.findRecent(userId, size);
    }

    // 모델 버전 번호: 처음 보는 버전이면 등록한다 (DB 변경 파일 없이 — 같은 버전이 동시에 와도 INSERT IGNORE)
    private Long modelVersionId(String versionLabel) {
        Long id = diagnosisMapper.findModelVersionId(MODEL_NAME, versionLabel);
        if (id == null) {
            diagnosisMapper.insertModelVersion(MODEL_NAME, versionLabel);
            id = diagnosisMapper.findModelVersionId(MODEL_NAME, versionLabel);
        }
        return id;
    }
}
