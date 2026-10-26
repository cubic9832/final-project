package com.kh.back.admin.dto;

import java.time.LocalDate;
import java.util.List;

/**
 * 7단계: 관리자 대시보드 회원 현황.
 *
 * @param total        전체 회원 수
 * @param admins       관리자 수
 * @param newLast7Days 최근 7일(오늘 포함) 가입 수
 * @param google       구글로 로그인할 수 있는 회원 수 (구글 전용 + 연결)
 * @param daily        최근 7일 날짜별 가입 수 (가입이 없는 날은 0)
 * @param ageBands     나이대별 회원 수 ("미입력" 포함)
 * @param genders      성별 회원 수 (MALE · FEMALE · NONE · 미입력)
 */
public record AdminMemberSummary(int total, int admins, int newLast7Days, int google,
                                 List<DailyCount> daily, List<GroupCount> ageBands, List<GroupCount> genders) {

    public record DailyCount(LocalDate date, int count) {
    }

    public record GroupCount(String label, int count) {
    }
}
