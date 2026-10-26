package com.kh.back.admin.controller;

import com.kh.back.admin.dto.AdminMemberResponse;
import com.kh.back.admin.dto.AdminMemberSummary;
import com.kh.back.admin.dto.RoleChangeRequest;
import com.kh.back.admin.service.AdminMemberService;
import com.kh.back.common.dto.ApiResponse;
import com.kh.back.common.dto.PageMeta;
import jakarta.validation.Valid;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 7단계: 관리자 회원 관리 · 회원 현황 · 관리자 권한 주기 / 빼기.
 * /api/v1/admin/** 는 SecurityConfig 에서 관리자 · 총관리자만, 권한 바꾸기(PATCH …/role)는 총관리자만 허용한다.
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

    // PATCH /api/v1/admin/members/{id}/role — 본문 { role: "ADMIN" | "USER" }. 총관리자만 (일반 관리자 403)
    // 호출: AdminMembersPanel.jsx 회원 상세 [관리자로 지정] · [관리자 해제] → adminApi.changeMemberRole
    @PatchMapping("/{id}/role")
    public ApiResponse<Void> changeRole(@AuthenticationPrincipal Long userId, @PathVariable Long id,
                                        @Valid @RequestBody RoleChangeRequest request) {
        adminMemberService.changeRole(userId, id, request.getRole());
        return ApiResponse.ok(null);
    }
}
