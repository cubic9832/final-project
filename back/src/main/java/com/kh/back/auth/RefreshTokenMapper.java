package com.kh.back.auth;

import java.time.LocalDateTime;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface RefreshTokenMapper {

    void insert(RefreshTokenDto refreshToken);

    RefreshTokenDto findByToken(String token);

    // 재발급(교체) · 로그아웃 때 사용. 지운 행 수를 돌려준다
    int deleteByToken(String token);

    // 보완 7 추가: 비밀번호를 바꾸면 그 회원의 refresh token 을 모두 지운다 (다른 기기 로그인 끊기)
    int deleteByUserId(Long userId);

    // 10-20: 만료된 refresh token 정리 (RefreshTokenCleanup 이 매일 새벽 호출). 지운 행 수를 돌려준다
    int deleteExpired(LocalDateTime now);

    // 6단계: 로그인된 기기 목록 (기한이 남은 토큰만, 최근에 쓴 순서)
    List<RefreshTokenDto> findActiveByUserId(@Param("userId") Long userId, @Param("now") LocalDateTime now);

    // 6단계: 기기 하나 로그아웃 — 주인 확인용으로 먼저 찾는다
    RefreshTokenDto findById(Long id);

    int deleteById(Long id);

    // 6단계: 다른 기기 모두 로그아웃 — 지금 기기(keepToken)만 남기고 지운다. 지운 행 수를 돌려준다
    int deleteOthers(@Param("userId") Long userId, @Param("keepToken") String keepToken);
}
