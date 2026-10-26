package com.kh.back.auth.mapper;

import com.kh.back.auth.dto.EmailVerificationDto;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

// 이메일 인증 코드 (보완 7). SQL 은 resources/mappers/EmailVerificationMapper.xml
@Mapper
public interface EmailVerificationMapper {

    EmailVerificationDto findByEmail(String email);

    // 처음이면 넣고, 있으면 새 코드로 덮어쓴다 (틀린 횟수 · 인증 완료는 초기화)
    int save(EmailVerificationDto verification);

    int increaseFailedAttempts(String email);

    int markVerified(@Param("email") String email);

    // 가입이 끝나면 지운다
    int deleteByEmail(String email);
}
