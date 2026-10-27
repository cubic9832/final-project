package com.kh.back.diagnosis.controller;

import com.kh.back.common.dto.ApiResponse;
import com.kh.back.diagnosis.dto.DiagnosisSaveRequest;
import com.kh.back.diagnosis.dto.DiagnosisSummary;
import com.kh.back.diagnosis.service.DiagnosisService;
import jakarta.validation.Valid;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 내 재무 진단 기록. 로그인 필요 (SecurityConfig 의 나머지 요청 규칙). 회원 번호는 토큰에서만 꺼낸다.
 */
@RestController
@RequestMapping("/api/v1/members/me/diagnoses")
@RequiredArgsConstructor
public class DiagnosisApiController {

    private final DiagnosisService diagnosisService;

    // POST /api/v1/members/me/diagnoses — 진단 결과 저장. 호출: FinancialResultPage.jsx(결과가 보일 때 한 번) → memberApi.saveDiagnosis
    @PostMapping
    public ResponseEntity<ApiResponse<DiagnosisSummary>> save(@AuthenticationPrincipal Long userId,
                                                              @Valid @RequestBody DiagnosisSaveRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.ok(diagnosisService.save(userId, request)));
    }

    // GET /api/v1/members/me/diagnoses?size=3 — 최근 진단 (최신 순). 호출: MyPage.jsx "최근 재무 진단" 카드 → memberApi.getRecentDiagnoses
    @GetMapping
    public ApiResponse<List<DiagnosisSummary>> recent(@AuthenticationPrincipal Long userId,
                                                      @RequestParam(defaultValue = "3") int size) {
        return ApiResponse.ok(diagnosisService.getRecent(userId, Math.min(Math.max(size, 1), 20)));
    }
}
