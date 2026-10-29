package com.kh.back.diagnosis.service;

import com.kh.back.diagnosis.dto.DiagnosisSaveRequest;
import com.kh.back.diagnosis.dto.DiagnosisSummary;
import java.util.List;

// 재무 진단 기록: 결과 화면에서 저장 → 마이페이지 "최근 재무 진단" 에서 보기
public interface DiagnosisService {

    // 로그인한 회원의 진단 결과 한 건 저장 → 저장한 기록
    DiagnosisSummary save(Long userId, DiagnosisSaveRequest request);

    // 최근 진단 (최신 순, size 건)
    List<DiagnosisSummary> getRecent(Long userId, int size);
}
