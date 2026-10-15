package com.kh.back.auth.service;

import com.kh.back.auth.dto.LoginRequest;
import com.kh.back.auth.dto.SignupRequest;
import com.kh.back.auth.dto.TokenResponse;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.dto.MemberResponse;
import com.kh.back.member.mapper.MemberMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    // 일반 회원가입으로 만들어지는 역할. 관리자(ADMIN)는 회원가입으로 만들 수 없다
    private static final String DEFAULT_ROLE = "USER";

    private final MemberMapper memberMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;

    @Override
    @Transactional
    public MemberResponse signup(SignupRequest request) {
        String email = normalizeEmail(request.getEmail());

        if (memberMapper.findByEmail(email) != null) {
            throw emailDuplicated();
        }

        MemberDto member = new MemberDto();
        member.setEmail(email);
        member.setPasswordHash(passwordEncoder.encode(request.getPassword())); // 원래 비밀번호는 저장하지 않는다
        member.setNickName(request.getNickName().trim());
        member.setRole(DEFAULT_ROLE);

        try {
            memberMapper.insert(member); // 이후 member.getId() 에 새 번호가 들어 있다
        } catch (DuplicateKeyException e) {
            // 위의 중복 확인과 저장 사이에 같은 이메일이 먼저 가입된 경우 (users.email UNIQUE)
            throw emailDuplicated();
        }

        return MemberResponse.from(member);
    }

    @Override
    @Transactional(readOnly = true)
    public TokenResponse login(LoginRequest request) {
        MemberDto member = memberMapper.findByEmail(normalizeEmail(request.getEmail()));

        // 이메일이 없을 때와 비밀번호가 틀렸을 때 같은 메시지를 쓴다 → 어떤 이메일이 가입되어 있는지 알려 주지 않기 위해
        if (member == null || !passwordEncoder.matches(request.getPassword(), member.getPasswordHash())) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "LOGIN_FAILED", "이메일 또는 비밀번호가 올바르지 않습니다.");
        }

        // 회원 번호와 역할을 담은 access token(JWT) 발급 (유효 시간: application.yml 의 jwt.access-token-validity)
        String accessToken = jwtProvider.createAccessToken(member.getId(), member.getRole());
        return new TokenResponse(accessToken, MemberResponse.from(member));
    }

    // 앞뒤 공백을 지우고 소문자로 맞춘다 → "User@Example.com " 과 "user@example.com" 을 같은 이메일로 본다
    // 회원가입과 로그인이 같은 규칙을 써야 대소문자를 다르게 입력해도 로그인된다
    private String normalizeEmail(String email) {
        return email.trim().toLowerCase();
    }

    private ApiException emailDuplicated() {
        return new ApiException(HttpStatus.CONFLICT, "EMAIL_DUPLICATED", "이미 가입된 이메일입니다.");
    }
}
