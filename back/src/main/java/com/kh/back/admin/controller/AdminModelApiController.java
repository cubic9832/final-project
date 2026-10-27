package com.kh.back.admin.controller;

import com.kh.back.admin.dto.AdminModelReport;
import com.kh.back.admin.service.AdminModelService;
import com.kh.back.common.dto.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 7단계: 관리자 모델 관리 — 학습 · 평가 결과와 모델 버전 기록. 관리자 · 총관리자 (SecurityConfig /api/v1/admin/**).
 */
@RestController
@RequestMapping("/api/v1/admin/model-report")
@RequiredArgsConstructor
public class AdminModelApiController {

    private final AdminModelService adminModelService;

    // GET /api/v1/admin/model-report — 호출: AdminModelsPanel.jsx → adminApi.getModelReport
    @GetMapping
    public ApiResponse<AdminModelReport> report() {
        return ApiResponse.ok(adminModelService.getReport());
    }
}
