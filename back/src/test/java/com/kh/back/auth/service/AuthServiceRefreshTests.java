package com.kh.back.auth.service;

import com.kh.back.auth.dto.AuthTokens;
import com.kh.back.auth.dto.RefreshTokenDto;
import com.kh.back.auth.mapper.RefreshTokenMapper;
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.mapper.MemberMapper;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import java.time.Duration;
import java.time.LocalDateTime;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

// 6단계: refresh token 재발급은 행을 새로 만들지 않고 같은 행(기기)의 토큰 값만 바꾼다
// → 로그인된 기기 번호가 바뀌지 않아, 다른 기기에서 미리 열어 둔 목록으로도 로그아웃할 수 있다
@ExtendWith(MockitoExtension.class)
class AuthServiceRefreshTests {

    @Mock MemberMapper memberMapper;
    @Mock RefreshTokenMapper refreshTokenMapper;
    @Mock JwtProvider jwtProvider;
    @InjectMocks AuthServiceImpl authService;

    @BeforeEach
    void setUp() {
        RefreshTokenDto saved = new RefreshTokenDto();
        saved.setId(5L);
        saved.setUserId(7L);
        saved.setToken("old-token");
        saved.setExpiresAt(LocalDateTime.now().plusDays(1));
        when(refreshTokenMapper.findByToken("old-token")).thenReturn(saved);

        MemberDto member = new MemberDto();
        member.setId(7L);
        member.setRole("USER");
        when(memberMapper.findById(7L)).thenReturn(member);
    }

    @Test
    void 재발급은_같은_행의_토큰만_바꾸고_새_행을_만들지_않는다() {
        when(jwtProvider.getRefreshTokenValidity()).thenReturn(Duration.ofDays(14));
        when(refreshTokenMapper.rotate(eq("old-token"), anyString(), any(), any())).thenReturn(1);

        AuthTokens tokens = authService.refresh("old-token");

        assertThat(tokens.getRefreshToken()).isNotEqualTo("old-token");
        verify(refreshTokenMapper, never()).insert(any());
        verify(refreshTokenMapper, never()).deleteByToken(any());
    }

    @Test
    void 같은_토큰으로_동시에_두_번_오면_하나만_통과한다() {
        when(jwtProvider.getRefreshTokenValidity()).thenReturn(Duration.ofDays(14));
        when(refreshTokenMapper.rotate(eq("old-token"), anyString(), any(), any())).thenReturn(0); // 이미 다른 요청이 바꿈

        assertThatThrownBy(() -> authService.refresh("old-token"))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("REFRESH_INVALID"));
    }
}
