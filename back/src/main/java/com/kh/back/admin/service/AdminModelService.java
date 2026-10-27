package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminModelReport;

// 7단계: 관리자 모델 관리 — 추천 서버가 쓰는 학습 · 평가 결과와 모델 버전 기록
public interface AdminModelService {

    AdminModelReport getReport();
}
