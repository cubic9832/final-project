package com.kh.back.auth.mapper;

import com.kh.back.auth.dto.RefreshTokenDto;

import java.time.LocalDateTime;
import org.apache.ibatis.annotations.Mapper;

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
}
