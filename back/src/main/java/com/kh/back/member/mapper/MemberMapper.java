package com.kh.back.member.mapper;

import com.kh.back.member.dto.MemberDto;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MemberMapper {

    MemberDto findById(Long id);

    MemberDto findByEmail(String email);

    // 실행 후 member.id 에 DB 가 만든 번호가 채워진다 (XML 의 useGeneratedKeys)
    void insert(MemberDto member);
}
