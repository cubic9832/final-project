package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminOverview;
import com.kh.back.admin.dto.AdminOverview.DailyCount;
import com.kh.back.admin.dto.AdminOverview.DiagnosisStats;
import com.kh.back.admin.dto.GroupCountRow;
import com.kh.back.admin.mapper.AdminOverviewMapper;
import com.kh.back.auth.service.LoginAttemptLimiter;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AdminOverviewServiceImpl implements AdminOverviewService {

    private static final int TREND_DAYS = 7;

    private final AdminOverviewMapper adminOverviewMapper;
    private final LoginAttemptLimiter loginAttemptLimiter; // 로그인 잠금은 서버 메모리에 있다 (보완 6)

    @Override
    @Transactional(readOnly = true)
    public AdminOverview getOverview() {
        LocalDate firstDay = LocalDate.now().minusDays(TREND_DAYS - 1L);

        // 날짜별 진단 수: 진단이 없는 날도 0 으로 채워 7칸 (회원 관리의 가입 추이와 같은 방식)
        Map<String, Integer> byDay = adminOverviewMapper.countDailyDiagnoses(firstDay.atStartOfDay()).stream()
                .collect(Collectors.toMap(GroupCountRow::getLabel, GroupCountRow::getCount));
        List<DailyCount> daily = new ArrayList<>();
        for (int i = 0; i < TREND_DAYS; i++) {
            LocalDate day = firstDay.plusDays(i);
            daily.add(new DailyCount(day, byDay.getOrDefault(day.toString(), 0)));
        }

        DiagnosisStats diagnoses = new DiagnosisStats(
                adminOverviewMapper.countDiagnoses(),
                daily.stream().mapToInt(DailyCount::count).sum(),
                adminOverviewMapper.countDiagnosedMembers(),
                adminOverviewMapper.averageMonthlyAvailable(),
                daily);
        return new AdminOverview(adminOverviewMapper.countProfileMissing(), loginAttemptLimiter.lockedCount(), diagnoses);
    }
}
