package com.kh.back.member.mapper;

import java.util.Set;
import org.apache.ibatis.annotations.Param;

import com.kh.back.member.dto.UserProfileDto;

import org.apache.ibatis.annotations.Mapper;

// 회원 개인 정보(user_profiles). SQL 은 resources/mappers/UserProfileMapper.xml (보완 5)
@Mapper
public interface UserProfileMapper {

    UserProfileDto findByUserId(Long userId); // 없으면 null (보완 5 이전 가입 회원 · 구글 가입 회원)

    int insert(UserProfileDto profile);

    // 6단계: 개인정보 수정 — 행이 없으면 만들고 있으면 바꾼다 (구글 가입 회원은 처음 저장할 때 행이 생긴다)
    // fields: 이번 요청에서 바꾼 칸 이름(birthDate · gender · phone · drivingExperience · purchaseTiming)
    // → 이미 있는 행은 그 칸만 고친다 (다른 기기에서 동시에 다른 칸을 저장해도 서로 덮어쓰지 않게)
    int upsert(@Param("p") UserProfileDto profile, @Param("fields") Set<String> fields);
}
