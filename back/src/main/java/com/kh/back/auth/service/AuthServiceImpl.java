package com.kh.back.auth.service;

import com.kh.back.auth.dto.AuthTokens;
import com.kh.back.auth.dto.LoginRequest;
import com.kh.back.auth.dto.RefreshTokenDto;
import com.kh.back.auth.dto.SignupRequest;
import com.kh.back.auth.mapper.RefreshTokenMapper;
import com.kh.back.auth.validation.PasswordPolicy;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.dto.MemberResponse;
import com.kh.back.member.mapper.MemberMapper;
import java.time.LocalDateTime;
import java.util.UUID;
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
    private final RefreshTokenMapper refreshTokenMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;

    @Override
    @Transactional
    public MemberResponse signup(SignupRequest request) {
        String email = normalizeEmail(request.getEmail());

        // 보완 2: 반복 · 연속 문자, 이메일 아이디 포함, 흔한 비밀번호 금지 (길이 · 문자 종류는 SignupRequest 가 먼저 검사)
        String passwordViolation = PasswordPolicy.check(request.getPassword(), email);
        if (passwordViolation != null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "PASSWORD_POLICY", passwordViolation);
        }

        if (memberMapper.findByEmail(email) != null) {
            throw emailDuplicated();
        }
        String nickName = request.getNickName().trim();
        if (memberMapper.countByNickName(nickName) > 0) {
            throw nickNameDuplicated(); // 보완 3: 닉네임 중복 금지 (V7 UNIQUE)
        }

        MemberDto member = new MemberDto();
        member.setEmail(email);
        member.setPasswordHash(passwordEncoder.encode(request.getPassword())); // 원래 비밀번호는 저장하지 않는다
        member.setNickName(nickName);
        member.setRole(DEFAULT_ROLE);

        try {
            memberMapper.insert(member); // 이후 member.getId() 에 새 번호가 들어 있다
        } catch (DuplicateKeyException e) {
            // 위의 중복 확인과 저장 사이에 같은 이메일 · 닉네임이 먼저 가입된 경우 (UNIQUE 위반)
            // 어느 쪽이 겹쳤는지는 DB 오류 문구의 키 이름으로 구분한다
            String reason = String.valueOf(e.getMessage());
            throw reason.contains("uq_users_nick_name") ? nickNameDuplicated() : emailDuplicated();
        }

        return MemberResponse.from(member);
    }

    // 보완 3: [중복 확인] 버튼 — 형식이 맞고 아직 가입되지 않은 이메일이면 true
    @Override
    @Transactional(readOnly = true)
    public boolean isEmailAvailable(String email) {
        String normalized = email == null ? "" : normalizeEmail(email);
        if (normalized.isEmpty() || normalized.length() > 100 || !normalized.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "이메일 형식이 올바르지 않습니다.");
        }
        return memberMapper.findByEmail(normalized) == null;
    }

    // 보완 3: [중복 확인] 버튼 — 2~12자이고 아직 쓰는 사람이 없는 닉네임이면 true
    @Override
    @Transactional(readOnly = true)
    public boolean isNickNameAvailable(String nickName) {
        String trimmed = nickName == null ? "" : nickName.trim();
        if (trimmed.length() < 2 || trimmed.length() > 12) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "이름 또는 닉네임은 2~12자로 입력해 주세요.");
        }
        return memberMapper.countByNickName(trimmed) == 0;
    }

    @Override
    @Transactional
    public AuthTokens login(LoginRequest request) {
        MemberDto member = memberMapper.findByEmail(normalizeEmail(request.getEmail()));

        // 이메일이 없을 때와 비밀번호가 틀렸을 때 같은 메시지를 쓴다 → 어떤 이메일이 가입되어 있는지 알려 주지 않기 위해
        if (member == null || !passwordEncoder.matches(request.getPassword(), member.getPasswordHash())) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "LOGIN_FAILED", "이메일 또는 비밀번호가 올바르지 않습니다.");
        }
        return issueTokens(member);
    }

    @Override
    @Transactional
    public AuthTokens refresh(String refreshToken) {
        if (refreshToken == null || refreshToken.isBlank()) {
            throw refreshInvalid(); // 쿠키가 없음 = 로그인한 적 없거나 로그아웃한 브라우저
        }

        RefreshTokenDto saved = refreshTokenMapper.findByToken(refreshToken);
        // DB 에 없으면 로그아웃했거나 이미 한 번 쓴(교체된) 토큰, 기간이 지났으면 만료된 토큰
        if (saved == null || saved.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw refreshInvalid();
        }

        // 한 번 쓴 refresh token 은 지우고 새로 발급한다 (rotation → 훔친 토큰을 오래 쓰지 못하게)
        // 같은 토큰으로 동시에 두 번 요청이 와도 지우기에 성공한 한 요청만 통과한다
        if (refreshTokenMapper.deleteByToken(refreshToken) == 0) {
            throw refreshInvalid();
        }

        MemberDto member = memberMapper.findById(saved.getUserId());
        if (member == null) {
            throw refreshInvalid();
        }
        return issueTokens(member);
    }

    @Override
    @Transactional
    public void logout(String refreshToken) {
        if (refreshToken != null && !refreshToken.isBlank()) {
            refreshTokenMapper.deleteByToken(refreshToken); // DB 에서 지우면 그 refresh token 으로는 더 이상 재발급할 수 없다
        }
    }

    // access token(JWT) 과 refresh token(무작위 문자열)을 함께 발급한다
    private AuthTokens issueTokens(MemberDto member) {
        // 회원 번호와 역할을 담은 access token(JWT) 발급 (유효 시간: application.yml 의 jwt.access-token-validity)
        String accessToken = jwtProvider.createAccessToken(member.getId(), member.getRole());

        // refresh token 은 JWT 가 아니라 추측할 수 없는 무작위 값(UUID)이고, DB 에 저장해 두고 비교한다
        RefreshTokenDto refresh = new RefreshTokenDto();
        refresh.setUserId(member.getId());
        refresh.setToken(UUID.randomUUID().toString());
        refresh.setExpiresAt(LocalDateTime.now().plus(jwtProvider.getRefreshTokenValidity()));
        refreshTokenMapper.insert(refresh);

        return new AuthTokens(accessToken, refresh.getToken(), MemberResponse.from(member));
    }

    private ApiException refreshInvalid() {
        return new ApiException(HttpStatus.UNAUTHORIZED, "REFRESH_INVALID", "다시 로그인해 주세요.");
    }

    // 앞뒤 공백을 지우고 소문자로 맞춘다 → "User@Example.com " 과 "user@example.com" 을 같은 이메일로 본다
    // 회원가입과 로그인이 같은 규칙을 써야 대소문자를 다르게 입력해도 로그인된다
    private String normalizeEmail(String email) {
        return email.trim().toLowerCase();
    }

    private ApiException emailDuplicated() {
        return new ApiException(HttpStatus.CONFLICT, "EMAIL_DUPLICATED", "이미 가입된 이메일입니다.");
    }

    private ApiException nickNameDuplicated() {
        return new ApiException(HttpStatus.CONFLICT, "NICKNAME_DUPLICATED", "이미 사용 중인 닉네임입니다.");
    }
}
