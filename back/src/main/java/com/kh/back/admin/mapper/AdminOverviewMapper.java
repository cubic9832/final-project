package com.kh.back.admin.mapper;

import com.kh.back.admin.dto.GroupCountRow;
import java.time.LocalDateTime;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

// 7단계: 관리자 운영 현황 — 할 일 · 재무 진단 이용 현황 (읽기만)
@Mapper
public interface AdminOverviewMapper {

    // 생년월일 또는 성별이 비어 있는 회원 수 (user_profiles 행이 없는 회원 포함)
    int countProfileMissing();

    int countDiagnoses();

    int countDiagnosesSince(@Param("since") LocalDateTime since);

    int countDiagnosedMembers();

    Long averageMonthlyAvailable();

    // 날짜별 진단 수 (label = yyyy-MM-dd)
    List<GroupCountRow> countDailyDiagnoses(@Param("since") LocalDateTime since);
}
