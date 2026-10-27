package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminAuditLogResponse;
import java.util.List;

// 7단계: 운영 로그 (관리자 작업 기록) 보기. 기록은 각 작업(예: 권한 바꾸기)이 같은 트랜잭션에서 남긴다
public interface AdminAuditLogService {

    // 최근 순 한 페이지 (page 는 1부터). action 이 비어 있으면 전체
    List<AdminAuditLogResponse> getLogs(String action, int page, int size);

    int countLogs(String action);
}
