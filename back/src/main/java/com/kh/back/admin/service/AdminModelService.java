package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminCandidate;
import com.kh.back.admin.dto.AdminModelReport;
import java.util.List;

// 7단계: 관리자 모델 관리 · 추천 관리 — 추천 서버가 쓰는 학습 결과 폴더(읽기만)와 모델 버전 기록
public interface AdminModelService {

    AdminModelReport getReport();

    // 추천 후보 차량 전체 (catalog.json). 폴더를 찾지 못하면 빈 목록
    List<AdminCandidate> getCandidates();
}
