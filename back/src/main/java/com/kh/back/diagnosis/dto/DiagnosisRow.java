package com.kh.back.diagnosis.dto;

import lombok.Getter;
import lombok.Setter;

/**
 * 재무 진단 저장용 한 묶음 (DB 쓰기 전용). 처음 설계 때 만든 표 3개에 나눠 넣는다 (V1, 새 DB 변경 없음)
 * input_snapshots(누가 · 언제) → financial_profiles(소득 · 지출 · 예금) → analysis_runs(결과)
 * snapshotId · analysisId 는 INSERT 때 DB 가 만든 번호가 채워진다 (useGeneratedKeys)
 */
@Getter
@Setter
public class DiagnosisRow {
    private Long snapshotId;
    private Long analysisId;
    private Long userId;
    private Long modelVersionId;
    private Long monthlyIncome;
    private Long monthlyExpense;
    private Long monthlyAvailable;
    private Long purchaseFunds;
    private Long priceUpper;
}
