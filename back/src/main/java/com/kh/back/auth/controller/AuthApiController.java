package com.kh.back.auth.controller;

import com.kh.back.auth.dto.SignupRequest;
import com.kh.back.auth.service.AuthService;
import com.kh.back.common.dto.ApiResponse;
import com.kh.back.member.dto.MemberResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 회원가입 · 로그인 (재발급 · 로그아웃은 refresh token 단계에서 추가).
 * 이 주소들은 로그인 전에도 불러야 하므로 SecurityConfig 에서 /api/v1/auth/** 를 공개해 두었다.
 */
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthApiController {

    private final AuthService authService;

    // POST /api/v1/auth/signup — 회원가입. 성공하면 201 과 가입한 회원 정보
    @PostMapping("/signup")
    public ResponseEntity<ApiResponse<MemberResponse>> signup(@Valid @RequestBody SignupRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.ok(authService.signup(request)));
    }
}
