package com.kh.back.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.member.MemberDto;
import com.kh.back.member.MemberMapper;
import com.kh.back.member.UserProfileMapper;
import java.time.Duration;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

// 보완 8: 구글 로그인 흐름 (구글 확인은 가짜로 바꿔서 Client ID 없이 확인)
@ExtendWith(MockitoExtension.class)
class AuthServiceGoogleTests {

    @Mock MemberMapper memberMapper;
    @Mock RefreshTokenMapper refreshTokenMapper;
    @Mock PasswordEncoder passwordEncoder;
    @Mock JwtProvider jwtProvider;
    @Mock UserProfileMapper userProfileMapper;
    @Mock LoginAttemptLimiter loginAttemptLimiter;
    @Mock RecaptchaVerifier recaptchaVerifier;
    @Mock EmailVerificationService emailVerificationService;
    @Mock GoogleTokenVerifier googleTokenVerifier;
    @Mock SocialAccountMapper socialAccountMapper;
    @InjectMocks AuthServiceImpl authService;

    private final GoogleTokenVerifier.GoogleUser google =
            new GoogleTokenVerifier.GoogleUser("google-sub-1", "g.user@gmail.com", "구글사용자");

    @BeforeEach
    void setUp() {
        // 대부분의 테스트가 쓰는 기본 구글 사용자 (외부 이메일 테스트는 다른 토큰을 써서 lenient)
        org.mockito.Mockito.lenient().when(googleTokenVerifier.verify("id-token")).thenReturn(google);
    }

    private MemberDto member(long id, String email, String passwordHash) {
        MemberDto m = new MemberDto();
        m.setId(id);
        m.setEmail(email);
        m.setNickName("닉네임" + id);
        m.setRole("USER");
        m.setPasswordHash(passwordHash);
        return m;
    }

    private void tokensWork() {
        when(jwtProvider.createAccessToken(anyLong(), any())).thenReturn("access");
        when(jwtProvider.getRefreshTokenValidity()).thenReturn(Duration.ofDays(14));
    }

    @Test
    void 연결된_구글계정이면_바로_로그인() {
        tokensWork();
        when(socialAccountMapper.findUserId("GOOGLE", "google-sub-1")).thenReturn(7L);
        when(memberMapper.findById(7L)).thenReturn(member(7, "g.user@gmail.com", "SOCIAL_ONLY"));

        AuthTokens tokens = authService.googleLogin("id-token", false); // 기존 회원은 동의 체크와 상관없다

        assertThat(tokens.getMember().getId()).isEqualTo(7L);
        assertThat(tokens.getMember().isSocialOnly()).isTrue();
    }

    @Test
    void 같은_이메일로_가입한_회원이면_자동연결_후_로그인() {
        tokensWork();
        when(memberMapper.findByEmail("g.user@gmail.com")).thenReturn(member(3, "g.user@gmail.com", "$2a$bcrypt"));

        AuthTokens tokens = authService.googleLogin("id-token", false);

        assertThat(tokens.getMember().getId()).isEqualTo(3L);
        assertThat(tokens.getMember().isSocialOnly()).isFalse(); // 비밀번호도 그대로 쓸 수 있다
        verify(socialAccountMapper).insert(3L, "GOOGLE", "google-sub-1", "g.user@gmail.com");
    }

    @Test
    void 처음_온_사람이_동의하지_않으면_가입하지_않는다() {
        assertThatThrownBy(() -> authService.googleLogin("id-token", false))
                .isInstanceOf(ApiException.class).hasMessageContaining("동의");
        verify(memberMapper, never()).insert(any());
    }

    @Test
    void 처음_온_사람이_동의하면_바로_가입하고_닉네임은_구글이름() {
        tokensWork();
        doAnswer(inv -> { ((MemberDto) inv.getArgument(0)).setId(11L); return null; }).when(memberMapper).insert(any());

        AuthTokens tokens = authService.googleLogin("id-token", true);

        assertThat(tokens.getMember().isSocialOnly()).isTrue();
        assertThat(tokens.getMember().getEmail()).isEqualTo("g.user@gmail.com");
        assertThat(tokens.getMember().getNickName()).isEqualTo("구글사용자");
        verify(socialAccountMapper).insert(eq(11L), eq("GOOGLE"), eq("google-sub-1"), eq("g.user@gmail.com"));
        verify(userProfileMapper, never()).insert(any()); // 생년월일 · 성별은 마이페이지에서
    }

    @Test
    void 구글이름이_이미_쓰이면_회원_숫자_닉네임() {
        tokensWork();
        when(memberMapper.countByNickName("구글사용자")).thenReturn(1);
        doAnswer(inv -> { ((MemberDto) inv.getArgument(0)).setId(12L); return null; }).when(memberMapper).insert(any());

        AuthTokens tokens = authService.googleLogin("id-token", true);

        assertThat(tokens.getMember().getNickName()).matches("회원\\d{4}");
    }

    @Test
    void 외부_이메일은_자동연결하지_않는다() {
        when(googleTokenVerifier.verify("other-token"))
                .thenReturn(new GoogleTokenVerifier.GoogleUser("google-sub-2", "someone@naver.com", "외부"));
        when(memberMapper.findByEmail("someone@naver.com")).thenReturn(member(4, "someone@naver.com", "$2a$bcrypt"));

        assertThatThrownBy(() -> authService.googleLogin("other-token", true))
                .isInstanceOf(ApiException.class).hasMessageContaining("이메일 · 비밀번호로 로그인");
        verify(socialAccountMapper, never()).insert(anyLong(), any(), any(), any());
    }
}
