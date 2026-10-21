package com.kh.back.member;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface MemberMapper {

    MemberDto findById(Long id);

    MemberDto findByEmail(String email);

    // 같은 닉네임 회원 수 (보완 3 · 닉네임 중복 확인). 0 이면 사용 가능
    int countByNickName(String nickName);

    // 실행 후 member.id 에 DB 가 만든 번호가 채워진다 (XML 의 useGeneratedKeys)
    void insert(MemberDto member);

    // 보완 7 추가: 비밀번호 재설정
    int updatePasswordHash(@Param("id") Long id, @Param("passwordHash") String passwordHash);

    // 닉네임 변경 (보완 3 추가). UNIQUE(V7) 에 걸리면 DuplicateKeyException
    int updateNickName(@Param("id") Long id, @Param("nickName") String nickName);

    // ── 회원 탈퇴 (보완 4) — MemberServiceImpl.withdraw 에서 한 트랜잭션으로 순서대로 실행 ──
    // users 를 참조하는 데이터를 먼저 정리해야 회원을 지울 수 있다 (외래키)
    int deleteFavoriteVehicles(Long userId);   // 관심차량 삭제

    int deletePurchasePlans(Long userId);      // 구매계획 삭제

    int detachInputSnapshots(Long userId);     // 분석 입력 기록은 남기고 회원 연결만 끊음 (user_id = NULL)

    int deleteById(Long id);                   // 회원 삭제 (refresh_token 은 V6 ON DELETE CASCADE 로 함께 삭제)
}
