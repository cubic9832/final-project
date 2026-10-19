package com.kh.back.auth;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

// 소셜(구글) 계정 ↔ 회원 연결 (보완 8). 테이블은 V9 의 social_accounts
@Mapper
public interface SocialAccountMapper {

    // 연결된 회원 번호 (없으면 null)
    Long findUserId(@Param("provider") String provider, @Param("providerUserId") String providerUserId);

    int insert(@Param("userId") Long userId, @Param("provider") String provider,
               @Param("providerUserId") String providerUserId, @Param("email") String email);
}
