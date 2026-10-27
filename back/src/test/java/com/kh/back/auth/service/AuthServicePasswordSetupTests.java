package com.kh.back.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.auth.dto.AuthTokens;
import com.kh.back.auth.dto.PasswordSetupRequest;
import com.kh.back.auth.mapper.RefreshTokenMapper;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.mapper.MemberMapper;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

// 보완 10: 구글로만 가입한 회원이 로그인 + 가입 이메일 인증 후 비밀번호를 만든다 → 이메일 로그인도 가능
@ExtendWith(MockitoExtension.class)
class AuthServicePasswordSetupTests {

    private static final String EMAIL = "first.google@gmail.com";

    @Mock MemberMapper memberMapper;
    @Mock RefreshTokenMapper refreshTokenMapper;
    @Mock JwtProvider jwtProvider;
    @Mock PasswordEncoder passwordEncoder;
    @Mock EmailVerificationService emailVerificationService;
    @Mock EmailVerificationProofStore verificationProofStore;
    @InjectMocks AuthServiceImpl authService;

    private MemberDto member(String passwordHash) {
        MemberDto member = new MemberDto();
        member.setId(9L);
        member.setEmail(EMAIL);
        member.setRole("USER");
        member.setPasswordHash(passwordHash);
        when(memberMapper.findById(9L)).thenReturn(member);
        return member;
    }

    private PasswordSetupRequest request() {
        PasswordSetupRequest request = new PasswordSetupRequest();
        request.setNewPassword("Credit#Setup27");
        request.setVerificationToken("proof");
        return request;
    }

    @Test
    void 구글_전용_회원은_가입_이메일로_코드를_받는다() {
        member(MemberDto.SOCIAL_ONLY_PASSWORD);

        authService.sendPasswordSetupCode(9L);

        verify(emailVerificationService).sendCode(EMAIL);
    }

    @Test
    void 이미_비밀번호가_있으면_400_HAS_PASSWORD() {
        member("bcrypt-hash");

        assertThatThrownBy(() -> authService.sendPasswordSetupCode(9L))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("HAS_PASSWORD"));
        verify(emailVerificationService, never()).sendCode(anyString());
    }

    @Test
    void 인증을_안_했으면_저장하지_않는다() {
        member(MemberDto.SOCIAL_ONLY_PASSWORD);
        when(emailVerificationService.isVerified(EMAIL)).thenReturn(false);

        assertThatThrownBy(() -> authService.setupPassword(9L, request()))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("EMAIL_NOT_VERIFIED"));
        verify(memberMapper, never()).updatePasswordHash(anyLong(), anyString());
    }

    @Test
    void 인증_후_저장하면_다른_기기는_끊고_이_기기는_새_토큰() {
        member(MemberDto.SOCIAL_ONLY_PASSWORD);
        when(emailVerificationService.isVerified(EMAIL)).thenReturn(true);
        when(verificationProofStore.isValid("proof", EMAIL)).thenReturn(true);
        when(passwordEncoder.encode("Credit#Setup27")).thenReturn("new-hash");
        when(jwtProvider.getRefreshTokenValidity()).thenReturn(Duration.ofDays(14));

        AuthTokens tokens = authService.setupPassword(9L, request());

        verify(memberMapper).updatePasswordHash(9L, "new-hash");
        verify(refreshTokenMapper).deleteByUserId(9L);
        verify(refreshTokenMapper).insert(any());
        verify(verificationProofStore).remove("proof");
        assertThat(tokens.getMember().isSocialOnly()).isFalse(); // 화면이 바로 [변경] 버튼으로 바꿀 수 있게
    }
}
