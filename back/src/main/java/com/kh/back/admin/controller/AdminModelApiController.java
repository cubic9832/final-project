package com.kh.back.admin.controller;

import com.kh.back.admin.dto.AdminCandidate;
import com.kh.back.admin.dto.AdminModelReport;
import com.kh.back.admin.service.AdminModelService;
import com.kh.back.common.dto.ApiResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 7단계: 관리자 모델 관리 · 추천 관리 — 학습 · 평가 결과, 추천 후보 차량, 모델 버전 기록.
 * 관리자 · 총관리자 (SecurityConfig /api/v1/admin/**).
 */
@RestController
@RequestMapping("/api/v1/admin")
@RequiredArgsConstructor
public class AdminModelApiController {

    private final AdminModelService adminModelService;

    // GET /api/v1/admin/model-report — 호출: AdminModelsPanel.jsx → adminApi.getModelReport
    @GetMapping("/model-report")
    public ApiResponse<AdminModelReport> report() {
        return ApiResponse.ok(adminModelService.getReport());
    }

    // GET /api/v1/admin/recommendation-candidates — 추천 후보 차량 전체 (281건 정도라 화면이 검색 · 페이지를 나눈다)
    // 호출: AdminRecommendationsPanel.jsx → adminApi.getRecommendationCandidates
    @GetMapping("/recommendation-candidates")
    public ApiResponse<List<AdminCandidate>> candidates() {
        return ApiResponse.ok(adminModelService.getCandidates());
    }
}
