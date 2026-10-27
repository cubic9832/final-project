package com.kh.back.auth.service;

import com.kh.back.auth.dto.AuthTokens;
import com.kh.back.auth.dto.GoogleLoginResult;
import com.kh.back.auth.dto.GoogleSignupRequest;
import com.kh.back.auth.mapper.RefreshTokenMapper;
import com.kh.back.auth.mapper.SocialAccountMapper;

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
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.mapper.MemberMapper;
import com.kh.back.member.mapper.UserAgreementMapper;
import com.kh.back.member.mapper.UserProfileMapper;
import java.time.Duration;
import java.time.LocalDate;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
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
    @Mock UserAgreementMapper userAgreementMapper; // 보완 9
    @Mock LoginAttemptLimiter loginAttemptLimiter;
    @Mock RecaptchaVerifier recaptchaVerifier;
    @Mock EmailVerificationService emailVerificationService;
    @Mock GoogleTokenVerifier googleTokenVerifier;
    @Mock SocialAccountMapper socialAccountMapper;
    @Spy GoogleSignupStore googleSignupStore = new GoogleSignupStore(); // 가입 대기 번호는 진짜로 보관
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

    // 처음 온 사람: 구글 확인 → 가입 대기 번호 (아직 가입하지 않음)
    private String signupToken() {
        GoogleLoginResult result = authService.googleLogin("id-token");
        assertThat(result.tokens()).isNull();
        return result.signup().signupToken();
    }

    private GoogleSignupRequest signupRequest(String token, LocalDate birthDate) {
        GoogleSignupRequest r = new GoogleSignupRequest();
        r.setSignupToken(token);
        r.setBirthDate(birthDate);
        r.setGender("FEMALE");
        r.setPhone("010-2468-1357");
        r.setConsent(true);
        return r;
    }

    @Test
    void 연결된_구글계정이면_바로_로그인() {
        tokensWork();
        when(socialAccountMapper.findUserId("GOOGLE", "google-sub-1")).thenReturn(7L);
        when(memberMapper.findById(7L)).thenReturn(member(7, "g.user@gmail.com", "SOCIAL_ONLY"));

        AuthTokens tokens = authService.googleLogin("id-token").tokens();

        assertThat(tokens.isNewMember()).isFalse();
        assertThat(tokens.getMember().getId()).isEqualTo(7L);
        assertThat(tokens.getMember().isSocialOnly()).isTrue();
    }

    @Test
    void 같은_이메일로_가입한_회원이면_자동연결_후_로그인() {
        tokensWork();
        when(memberMapper.findByEmail("g.user@gmail.com")).thenReturn(member(3, "g.user@gmail.com", "$2a$bcrypt"));

        AuthTokens tokens = authService.googleLogin("id-token").tokens();

        assertThat(tokens.getMember().getId()).isEqualTo(3L);
        assertThat(tokens.getMember().isSocialOnly()).isFalse(); // 비밀번호도 그대로 쓸 수 있다
        verify(socialAccountMapper).insert(3L, "GOOGLE", "google-sub-1", "g.user@gmail.com");
    }

    @Test
    void 처음_온_사람은_가입하지_않고_가입_대기_번호를_준다() {
        GoogleLoginResult result = authService.googleLogin("id-token");

        assertThat(result.tokens()).isNull();
        assertThat(result.signup().signupToken()).isNotBlank();
        assertThat(result.signup().email()).isEqualTo("g.user@gmail.com");
        verify(memberMapper, never()).insert(any());
    }

    @Test
    void 추가_정보로_가입하면_닉네임은_구글이름이고_개인정보도_저장된다() {
        tokensWork();
        doAnswer(inv -> { ((MemberDto) inv.getArgument(0)).setId(11L); return null; }).when(memberMapper).insert(any());
        String token = signupToken();

        AuthTokens tokens = authService.googleSignup(signupRequest(token, LocalDate.of(1999, 7, 21)));

        assertThat(tokens.getMember().isSocialOnly()).isTrue();
        assertThat(tokens.getMember().getNickName()).isEqualTo("구글사용자");
        assertThat(tokens.isNewMember()).isTrue(); // 화면이 자동 닉네임 알림을 띄운다
        verify(userProfileMapper).insert(any());
        verify(userAgreementMapper).insert(any()); // 보완 9: 동의 시각 기록
        verify(socialAccountMapper).insert(eq(11L), eq("GOOGLE"), eq("google-sub-1"), eq("g.user@gmail.com"));
        // 1회용: 같은 번호로 다시 가입할 수 없다
        assertThatThrownBy(() -> authService.googleSignup(signupRequest(token, LocalDate.of(1999, 7, 21))))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("GOOGLE_SIGNUP_EXPIRED"));
    }

    @Test
    void 만18세_미만이면_가입하지_않는다() {
        String token = signupToken();

        assertThatThrownBy(() -> authService.googleSignup(signupRequest(token, LocalDate.now().minusYears(17))))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("AGE_RESTRICTED"));
        verify(memberMapper, never()).insert(any());
    }

    @Test
    void 구글이름이_이미_쓰이면_회원_숫자_닉네임() {
        tokensWork();
        when(memberMapper.countByNickName("구글사용자")).thenReturn(1);
        doAnswer(inv -> { ((MemberDto) inv.getArgument(0)).setId(12L); return null; }).when(memberMapper).insert(any());

        AuthTokens tokens = authService.googleSignup(signupRequest(signupToken(), LocalDate.of(1999, 7, 21)));

        assertThat(tokens.getMember().getNickName()).matches("회원\\d{4}");
    }

    @Test
    void 외부_이메일은_자동연결하지_않는다() {
        when(googleTokenVerifier.verify("other-token"))
                .thenReturn(new GoogleTokenVerifier.GoogleUser("google-sub-2", "someone@naver.com", "외부"));
        when(memberMapper.findByEmail("someone@naver.com")).thenReturn(member(4, "someone@naver.com", "$2a$bcrypt"));

        assertThatThrownBy(() -> authService.googleLogin("other-token"))
                .isInstanceOf(ApiException.class).hasMessageContaining("이메일 · 비밀번호로 로그인");
        verify(socialAccountMapper, never()).insert(anyLong(), any(), any(), any());
    }
}
