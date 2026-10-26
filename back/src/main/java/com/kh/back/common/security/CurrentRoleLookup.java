package com.kh.back.common.security;

import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.mapper.MemberMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/**
 * 7단계: 회원의 "지금" 권한을 DB 에서 읽는다.
 * access token 안의 role 은 로그인할 때의 값이라, 총관리자가 관리자를 해제해도 최대 30분 그대로 남는다.
 * 그래서 관리자 API(/api/v1/admin/**) 요청에서만 DB 를 한 번 더 본다 (JwtAuthenticationFilter).
 * 일반 API 는 토큰의 role 을 그대로 쓴다 (요청마다 DB 를 읽지 않도록).
 */
@Component
@RequiredArgsConstructor
public class CurrentRoleLookup {

    private final MemberMapper memberMapper;

    // 탈퇴해서 회원이 없으면 null
    public String currentRole(Long userId) {
        MemberDto member = memberMapper.findById(userId);
        return member == null ? null : member.getRole();
    }
}
