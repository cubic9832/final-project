package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminSystemStatus;

// 7단계: 관리자 운영 현황 — 서비스 연결 상태
public interface AdminSystemService {

    // DB 가 꺼져 있어도 예외 없이 databaseUp = false 로 돌려준다
    AdminSystemStatus getStatus();
}
