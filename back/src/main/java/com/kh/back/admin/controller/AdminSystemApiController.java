package com.kh.back.admin.controller;

import com.kh.back.admin.dto.AdminSystemStatus;
import com.kh.back.admin.service.AdminSystemService;
import com.kh.back.common.dto.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 7단계: 관리자 운영 현황의 서비스 연결 상태. 관리자 · 총관리자가 볼 수 있다 (SecurityConfig /api/v1/admin/**).
 */
@RestController
@RequestMapping("/api/v1/admin/system-status")
@RequiredArgsConstructor
public class AdminSystemApiController {

    private final AdminSystemService adminSystemService;

    // GET /api/v1/admin/system-status — Spring 켜진 시각 · MySQL 응답 여부 · 응답 시간 · Flyway 번호
    // 호출: AdminOverviewPanel.jsx → adminApi.getSystemStatus
    @GetMapping
    public ApiResponse<AdminSystemStatus> status() {
        return ApiResponse.ok(adminSystemService.getStatus());
    }
}
