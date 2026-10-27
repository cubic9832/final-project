package com.kh.back.admin.dto;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 7단계: 관리자 모델 관리 — 추천 서버가 쓰는 학습 결과(ml/outputs/models/...) 와 DB 의 모델 버전 기록.
 * 학습 파일을 찾지 못하면 available = false 이고 나머지 학습 값은 null (모델 버전 기록은 그대로).
 *
 * @param available          학습 결과 파일을 읽었는지
 * @param runName            학습 결과 폴더 이름 (예: 20261026-100k-v1)
 * @param schema             입력 구조 (metadata.json schema)
 * @param trainedAt          학습 파일(model.pt)을 만든 시각
 * @param profiles           학습에 쓴 가상 가구 수
 * @param candidateRows      후보 차량 행 수
 * @param preferencePairs    비교 쌍 수
 * @param splitProfiles      학습 · 검증 · 시험 가구 수
 * @param heldOutModels      학습에서 뺀(처음 보는) 차종 수
 * @param testPairAccuracy   시험 데이터 비교 정확도
 * @param financialViolations 재무 조건을 어긴 추천 수 (0 이어야 함)
 * @param meaning            평가 값의 뜻 (학습 파일의 설명 그대로)
 * @param metrics            이전 모델 대비 지표 (0~1)
 * @param history            에포크별 손실 · 검증 정확도
 * @param versions           DB 의 모델 버전과 그 버전으로 저장된 재무 진단 수
 */
public record AdminModelReport(boolean available, String runName, String schema, LocalDateTime trainedAt,
                               Long profiles, Long candidateRows, Long preferencePairs, SplitProfiles splitProfiles,
                               Integer heldOutModels, Double testPairAccuracy, Integer financialViolations, String meaning,
                               List<Metric> metrics, List<Epoch> history, List<Version> versions) {

    public record SplitProfiles(long train, long validation, long test) {
    }

    public record Metric(String name, double previous, double current) {
    }

    public record Epoch(int epoch, double loss, double validationPairAccuracy) {
    }

    public record Version(String versionLabel, String executionType, LocalDateTime createdAt, int diagnoses) {
    }
}
