package com.kh.back.member.mapper;

import com.kh.back.member.dto.UserProfileDto;

import org.apache.ibatis.annotations.Mapper;

// 회원 개인 정보(user_profiles). SQL 은 resources/mappers/UserProfileMapper.xml (보완 5)
@Mapper
public interface UserProfileMapper {

    UserProfileDto findByUserId(Long userId); // 없으면 null (보완 5 이전 가입 회원)

    int insert(UserProfileDto profile);
}
