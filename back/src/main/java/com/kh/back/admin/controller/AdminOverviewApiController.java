package com.kh.back.admin.controller;

import com.kh.back.admin.dto.AdminOverview;
import com.kh.back.admin.service.AdminOverviewService;
import com.kh.back.common.dto.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 7단계: 관리자 운영 현황 — 먼저 확인할 작업 · 재무 진단 이용 현황. 관리자 · 총관리자 (SecurityConfig /api/v1/admin/**).
 */
@RestController
@RequestMapping("/api/v1/admin/overview")
@RequiredArgsConstructor
public class AdminOverviewApiController {

    private final AdminOverviewService adminOverviewService;

    // GET /api/v1/admin/overview — 호출: AdminOverviewPanel.jsx → adminApi.getAdminOverview
    @GetMapping
    public ApiResponse<AdminOverview> overview() {
        return ApiResponse.ok(adminOverviewService.getOverview());
    }
}
