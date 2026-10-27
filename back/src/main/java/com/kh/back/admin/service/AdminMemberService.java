package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminMemberResponse;
import com.kh.back.admin.dto.AdminMemberSummary;
import java.util.List;

// 7단계: 관리자 회원 관리 · 회원 현황 + 총관리자의 관리자 권한 주기 · 빼기. 구현은 AdminMemberServiceImpl
public interface AdminMemberService {

    // 회원 목록 한 페이지 (page 는 1부터). keyword · role 은 비어 있으면 전체
    List<AdminMemberResponse> getMembers(String keyword, String role, int page, int size);

    int countMembers(String keyword, String role);

    // 대시보드 회원 현황 (전체 · 관리자 · 최근 7일 가입 · 구글 · 날짜별 · 나이대 · 성별)
    AdminMemberSummary getSummary();

    // 총관리자(actorId)가 회원(targetId)의 권한을 USER ↔ ADMIN 으로 바꾼다. 자기 자신 · 총관리자는 바꿀 수 없다
    void changeRole(Long actorId, Long targetId, String role);

    // 관리자가 회원의 로그인 실패 기록 · 잠금(보완 6)을 지운다. 운영 로그에 남긴다
    void unlockLogin(Long actorId, Long targetId);
}
