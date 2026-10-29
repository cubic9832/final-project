package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminOverview;

// 7단계: 관리자 운영 현황 — 먼저 확인할 작업 · 재무 진단 이용 현황
public interface AdminOverviewService {

    AdminOverview getOverview();
}
