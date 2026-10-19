package com.kh.back.auth;

import com.kh.back.auth.RefreshTokenDto;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface RefreshTokenMapper {

    void insert(RefreshTokenDto refreshToken);

    RefreshTokenDto findByToken(String token);

    // 재발급(교체) · 로그아웃 때 사용. 지운 행 수를 돌려준다
    int deleteByToken(String token);
}
