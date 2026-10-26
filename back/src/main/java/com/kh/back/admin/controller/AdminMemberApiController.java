package com.kh.back.admin.controller;

import com.kh.back.admin.dto.AdminMemberResponse;
import com.kh.back.admin.dto.AdminMemberSummary;
import com.kh.back.admin.service.AdminMemberService;
import com.kh.back.common.dto.ApiResponse;
import com.kh.back.common.dto.PageMeta;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 7단계: 관리자 회원 관리 · 회원 현황 (읽기 전용).
 * /api/v1/admin/** 는 SecurityConfig 에서 ADMIN 만 허용한다 (일반 회원 403, 비회원 401).
 */
@RestController
@RequestMapping("/api/v1/admin/members")
@RequiredArgsConstructor
public class AdminMemberApiController {

    private final AdminMemberService adminMemberService;

    // GET /api/v1/admin/members?keyword=&role=&page=1&size=10 — 회원 목록 (최근 가입 순) + 페이징 정보
    // 호출: AdminMembersPanel.jsx 화면이 열릴 때 · 검색 · 권한 선택 · 페이지 이동 → adminApi.getAdminMembers
    @GetMapping
    public ApiResponse<List<AdminMemberResponse>> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String role,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        page = Math.max(page, 1);
        size = Math.min(Math.max(size, 1), 50); // 한 번에 최대 50명
        List<AdminMemberResponse> members = adminMemberService.getMembers(keyword, role, page, size);
        int total = adminMemberService.countMembers(keyword, role);
        return ApiResponse.ok(members, PageMeta.of(page, size, total));
    }

    // GET /api/v1/admin/members/summary — 회원 현황 (전체 · 관리자 · 최근 7일 가입 · 구글 · 날짜별 · 나이대 · 성별)
    // 호출: AdminMembersPanel.jsx · AdminOverviewPanel.jsx → adminApi.getMemberSummary
    @GetMapping("/summary")
    public ApiResponse<AdminMemberSummary> summary() {
        return ApiResponse.ok(adminMemberService.getSummary());
    }
}
