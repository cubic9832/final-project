package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminMemberResponse;
import com.kh.back.admin.dto.AdminMemberSummary;
import java.util.List;

// 7단계: 관리자 회원 관리 · 회원 현황 (읽기 전용). 구현은 AdminMemberServiceImpl
public interface AdminMemberService {

    // 회원 목록 한 페이지 (page 는 1부터). keyword · role 은 비어 있으면 전체
    List<AdminMemberResponse> getMembers(String keyword, String role, int page, int size);

    int countMembers(String keyword, String role);

    // 대시보드 회원 현황 (전체 · 관리자 · 최근 7일 가입 · 구글 · 날짜별 · 나이대 · 성별)
    AdminMemberSummary getSummary();
}
