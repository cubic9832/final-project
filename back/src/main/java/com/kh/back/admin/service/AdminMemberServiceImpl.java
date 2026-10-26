package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminMemberResponse;
import com.kh.back.admin.dto.AdminMemberSummary;
import com.kh.back.admin.dto.AdminMemberSummary.DailyCount;
import com.kh.back.admin.dto.AdminMemberSummary.GroupCount;
import com.kh.back.admin.dto.GroupCountRow;
import com.kh.back.admin.mapper.AdminAuditLogMapper;
import com.kh.back.admin.mapper.AdminMemberMapper;
import com.kh.back.auth.mapper.RefreshTokenMapper;
import com.kh.back.auth.service.LoginAttemptLimiter;
import com.kh.back.common.exception.ApiException;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
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
    private final RefreshTokenMapper refreshTokenMapper;
    private final AdminAuditLogMapper adminAuditLogMapper; // V13: 운영 로그

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

    // 7단계: 관리자 권한 주기 · 빼기 (총관리자만 — SecurityConfig 에서 SUPER_ADMIN 만 이 주소를 통과시킨다)
    // 규칙: 자기 자신은 못 바꾼다(실수로 총관리자가 사라지지 않게), 총관리자는 못 바꾼다(DB 에서만)
    // 바꾼 뒤에는 그 회원의 로그인된 기기를 모두 로그아웃시킨다 → 다시 로그인하면 새 권한이 토큰에 들어간다
    //   (이미 받은 access token 은 최대 30분 그대로 — 5단계와 같은 한계)
    @Override
    @Transactional
    public void changeRole(Long actorId, Long targetId, String role) {
        if (actorId.equals(targetId)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "SELF_ROLE_CHANGE", "자기 자신의 권한은 바꿀 수 없습니다.");
        }
        String current = adminMemberMapper.findRole(targetId);
        if (current == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "MEMBER_NOT_FOUND", "회원을 찾을 수 없습니다.");
        }
        if ("SUPER_ADMIN".equals(current)) {
            throw new ApiException(HttpStatus.FORBIDDEN, "SUPER_ADMIN_PROTECTED", "총관리자의 권한은 바꿀 수 없습니다.");
        }
        if (current.equals(role)) {
            return; // 이미 그 권한이면 아무것도 하지 않는다
        }
        adminMemberMapper.updateRole(targetId, role);
        // 운영 로그: 누가 누구를 무엇으로 바꿨는지 (같은 트랜잭션 → 기록이 실패하면 권한 변경도 취소)
        adminAuditLogMapper.insert(actorId, "ROLE_CHANGE", "MEMBER", targetId, current + " → " + role);
        refreshTokenMapper.deleteByUserId(targetId);
    }

    // 7단계: 로그인 잠금 해제 — 보완 6 의 실패 횟수 · 10분 잠금은 서버 메모리에 이메일별로 있다 → 지우면 바로 로그인 가능
    // 관리자 · 총관리자 모두 할 수 있다 (본인 확인은 회원이 직접 비밀번호 찾기로 하는 것이 원칙, 이건 문의 대응용)
    @Override
    @Transactional
    public void unlockLogin(Long actorId, Long targetId) {
        String email = adminMemberMapper.findEmail(targetId);
        if (email == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "MEMBER_NOT_FOUND", "회원을 찾을 수 없습니다.");
        }
        loginAttemptLimiter.reset(email);
        adminAuditLogMapper.insert(actorId, "LOGIN_UNLOCK", "MEMBER", targetId, "로그인 잠금 해제");
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
