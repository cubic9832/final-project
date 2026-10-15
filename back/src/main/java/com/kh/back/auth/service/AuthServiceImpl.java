package com.kh.back.auth.service;

import com.kh.back.auth.dto.SignupRequest;
import com.kh.back.common.exception.ApiException;
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

    @Override
    @Transactional
    public MemberResponse signup(SignupRequest request) {
        // 앞뒤 공백을 지우고 소문자로 맞춘다 → "User@Example.com " 과 "user@example.com" 을 같은 이메일로 본다
        String email = request.getEmail().trim().toLowerCase();

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

    private ApiException emailDuplicated() {
        return new ApiException(HttpStatus.CONFLICT, "EMAIL_DUPLICATED", "이미 가입된 이메일입니다.");
    }
}
