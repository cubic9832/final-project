package com.kh.back.diagnosis.mapper;

import com.kh.back.diagnosis.dto.DiagnosisRow;
import com.kh.back.diagnosis.dto.DiagnosisSummary;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

// 재무 진단 기록 — V1 의 input_snapshots · financial_profiles · analysis_runs · model_versions 를 쓴다
@Mapper
public interface DiagnosisMapper {

    Long findModelVersionId(@Param("modelName") String modelName, @Param("versionLabel") String versionLabel);

    // 같은 이름 · 버전이 이미 있으면 아무것도 안 함 (UNIQUE uq_model_version)
    void insertModelVersion(@Param("modelName") String modelName, @Param("versionLabel") String versionLabel);

    void insertSnapshot(DiagnosisRow row);

    void insertFinancialProfile(DiagnosisRow row);

    void insertAnalysisRun(DiagnosisRow row);

    // 회원의 최근 진단 (최신 순)
    List<DiagnosisSummary> findRecent(@Param("userId") Long userId, @Param("size") int size);
}
