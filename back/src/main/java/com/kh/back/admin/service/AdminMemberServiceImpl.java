package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminMemberResponse;
import com.kh.back.admin.dto.AdminMemberSummary;
import com.kh.back.admin.dto.AdminMemberSummary.DailyCount;
import com.kh.back.admin.dto.AdminMemberSummary.GroupCount;
import com.kh.back.admin.dto.GroupCountRow;
import com.kh.back.admin.mapper.AdminMemberMapper;
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
public class AdminMemberServiceImpl implements AdminMemberService {

    private static final int TREND_DAYS = 7; // 가입 추이: 오늘 포함 최근 7일
    // 나이대 · 성별은 항상 이 순서로 보여 준다 (0명인 묶음도 0 으로)
    private static final List<String> AGE_BANDS = List.of("10대", "20대", "30대", "40대", "50대 이상", "미입력");
    private static final List<String> GENDERS = List.of("MALE", "FEMALE", "NONE", "미입력");

    private final AdminMemberMapper adminMemberMapper;
    private final LoginAttemptLimiter loginAttemptLimiter; // 보완 6: 로그인 5번 실패 잠금 (서버 메모리)

    @Override
    @Transactional(readOnly = true)
    public List<AdminMemberResponse> getMembers(String keyword, String role, int page, int size) {
        int offset = (page - 1) * size;
        return adminMemberMapper.findMembers(blankToNull(keyword), blankToNull(role), offset, size).stream()
                .map(row -> AdminMemberResponse.from(row, loginAttemptLimiter.lockedMinutesLeft(row.getEmail())))
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public int countMembers(String keyword, String role) {
        return adminMemberMapper.countMembers(blankToNull(keyword), blankToNull(role));
    }

    @Override
    @Transactional(readOnly = true)
    public AdminMemberSummary getSummary() {
        LocalDate firstDay = LocalDate.now().minusDays(TREND_DAYS - 1L);

        // 날짜별 가입 수: 가입이 없는 날도 0 으로 채워 7칸을 만든다 (차트가 비지 않게)
        Map<String, Integer> joins = toMap(adminMemberMapper.countDailyJoins(firstDay.atStartOfDay()));
        List<DailyCount> daily = new ArrayList<>();
        for (int i = 0; i < TREND_DAYS; i++) {
            LocalDate day = firstDay.plusDays(i);
            daily.add(new DailyCount(day, joins.getOrDefault(day.toString(), 0)));
        }
        int newLast7Days = daily.stream().mapToInt(DailyCount::count).sum();

        return new AdminMemberSummary(
                adminMemberMapper.countMembers(null, null),
                adminMemberMapper.countAdmins(),
                newLast7Days,
                adminMemberMapper.countGoogle(),
                daily,
                ordered(AGE_BANDS, toMap(adminMemberMapper.countAgeBands())),
                ordered(GENDERS, toMap(adminMemberMapper.countGenders())));
    }

    private static Map<String, Integer> toMap(List<GroupCountRow> rows) {
        return rows.stream().collect(Collectors.toMap(GroupCountRow::getLabel, GroupCountRow::getCount));
    }

    private static List<GroupCount> ordered(List<String> labels, Map<String, Integer> counts) {
        return labels.stream().map(label -> new GroupCount(label, counts.getOrDefault(label, 0))).toList();
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value.trim();
    }
}
