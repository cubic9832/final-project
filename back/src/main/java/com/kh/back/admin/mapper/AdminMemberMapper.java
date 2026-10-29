package com.kh.back.admin.mapper;

import com.kh.back.admin.dto.AdminMemberRow;
import com.kh.back.admin.dto.GroupCountRow;
import java.time.LocalDateTime;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

// 7단계: 관리자 회원 관리 · 회원 현황 SQL (권한 주기 · 빼기 grantAdmin · revokeAdmin 말고는 읽기만 한다)
@Mapper
public interface AdminMemberMapper {

    // 회원 목록 (최근 가입 순). keyword: 닉네임 · 이메일 일부, role: USER · ADMIN (null 이면 전체)
    List<AdminMemberRow> findMembers(@Param("keyword") String keyword, @Param("role") String role,
                                     @Param("offset") int offset, @Param("size") int size);

    int countMembers(@Param("keyword") String keyword, @Param("role") String role);

    int countAdmins(); // 관리자 + 총관리자

    String findRole(Long id);

    String findEmail(Long id); // 로그인 잠금 해제용 (없으면 null)

    // 보완 11: 권한은 admin_accounts(V21) — 지정은 넣기(있으면 바꾸기), 해제는 지우기
    int grantAdmin(@Param("id") Long id, @Param("role") String role, @Param("grantedBy") Long grantedBy);

    int revokeAdmin(Long id);

    int countJoinedSince(LocalDateTime since);

    int countGoogle();

    // 날짜(yyyy-MM-dd)별 가입 수 — since 이후만
    List<GroupCountRow> countDailyJoins(LocalDateTime since);

    // 나이대별 (10대 ~ 50대 이상, 생년월일이 없으면 "미입력")
    List<GroupCountRow> countAgeBands();

    // 성별 (MALE · FEMALE · NONE, 없으면 "미입력")
    List<GroupCountRow> countGenders();
}
