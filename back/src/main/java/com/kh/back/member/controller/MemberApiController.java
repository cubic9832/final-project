package com.kh.back.member.controller;

import com.kh.back.common.dto.ApiResponse;
import com.kh.back.member.dto.MemberResponse;
import com.kh.back.member.service.MemberService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 로그인한 회원 본인의 정보.
 * SecurityConfig 규칙상 /api/v1/members/** 는 로그인이 필요하다 → 토큰이 없으면 이 Controller 에 오기 전에 401.
 */
@RestController
@RequestMapping("/api/v1/members")
@RequiredArgsConstructor
public class MemberApiController {

    private final MemberService memberService;

    // GET /api/v1/members/me — 내 정보
    // 회원 번호는 요청 값으로 받지 않고, JwtAuthenticationFilter 가 토큰에서 꺼내 넣어 둔 값을 쓴다.
    // (요청 값으로 받으면 다른 사람 번호를 넣어 남의 정보를 볼 수 있기 때문)
    @GetMapping("/me")
    public ApiResponse<MemberResponse> me(@AuthenticationPrincipal Long userId) {
        return ApiResponse.ok(memberService.getMember(userId));
    }
}
