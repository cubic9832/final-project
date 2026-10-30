package com.kh.back.admin.dto;

import java.time.LocalDate;
import java.util.List;

/**
 * 7단계: 관리자 운영 현황 — "먼저 확인할 작업" 과 재무 진단 이용 현황 (모두 실제 데이터).
 *
 * @param profileMissing   생년월일 · 성별을 아직 입력하지 않은 회원 수 (구글 가입 직후 등)
 * @param lockedMembers    지금 로그인이 잠긴 이메일 수 (5번 실패, 10분)
 * @param diagnoses        재무 진단 이용 현황 (V1 analysis_runs)
 */
public record AdminOverview(int profileMissing, long lockedMembers, DiagnosisStats diagnoses) {

    /**
     * @param total               전체 진단 수
     * @param last7Days           최근 7일(오늘 포함) 진단 수
     * @param members             진단을 한 번이라도 한 회원 수 (탈퇴 회원 제외)
     * @param avgMonthlyAvailable 평균 구매 전 월 여유금 (원, 진단이 없으면 null)
     * @param daily               최근 7일 날짜별 진단 수 (없는 날은 0)
     */
    public record DiagnosisStats(int total, int last7Days, int members, Long avgMonthlyAvailable, List<DailyCount> daily) {
    }

    public record DailyCount(LocalDate date, int count) {
    }
}
