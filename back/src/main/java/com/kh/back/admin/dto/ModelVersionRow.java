package com.kh.back.admin.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.Setter;

// 7단계: model_versions 한 줄 + 그 버전으로 저장된 재무 진단 수 (SQL 결과)
@Getter
@Setter
public class ModelVersionRow {
    private String versionLabel;
    private String executionType;
    private LocalDateTime createdAt;
    private int diagnoses;
}
