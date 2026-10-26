package com.kh.back.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.common.exception.ApiException;
import java.time.LocalDateTime;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

// 6단계: 로그인된 기기 보기 · 기기별 로그아웃 · 다른 기기 모두 로그아웃
@ExtendWith(MockitoExtension.class)
class LoginSessionServiceTests {

    @Mock RefreshTokenMapper refreshTokenMapper;
    @InjectMocks LoginSessionService loginSessionService;

    private RefreshTokenDto token(long id, long userId, String value) {
        RefreshTokenDto t = new RefreshTokenDto();
        t.setId(id);
        t.setUserId(userId);
        t.setToken(value);
        t.setDevice("Chrome · Windows");
        t.setLoggedInAt(LocalDateTime.now().minusDays(1));
        t.setCreatedAt(LocalDateTime.now());
        return t;
    }

    @Test
    void 목록에서_지금_기기를_표시하고_토큰값은_내보내지_않는다() {
        when(refreshTokenMapper.findActiveByUserId(any(), any()))
                .thenReturn(List.of(token(1, 7, "this-device"), token(2, 7, "other-device")));

        List<LoginSessionResponse> sessions = loginSessionService.list(7L, "this-device");

        assertThat(sessions).extracting(LoginSessionResponse::current).containsExactly(true, false);
        assertThat(sessions).extracting(LoginSessionResponse::id).containsExactly(1L, 2L);
    }

    @Test
    void 남의_기기는_로그아웃할_수_없다_403() {
        when(refreshTokenMapper.findById(5L)).thenReturn(token(5, 99, "someone-else"));

        assertThatThrownBy(() -> loginSessionService.logout(7L, 5L, "this-device"))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("SESSION_FORBIDDEN"));
        verify(refreshTokenMapper, never()).deleteById(anyLong());
    }

    @Test
    void 없는_기기는_404_지금_기기는_헤더_로그아웃으로() {
        assertThatThrownBy(() -> loginSessionService.logout(7L, 3L, "this-device"))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("SESSION_NOT_FOUND"));

        when(refreshTokenMapper.findById(1L)).thenReturn(token(1, 7, "this-device"));
        assertThatThrownBy(() -> loginSessionService.logout(7L, 1L, "this-device"))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("CURRENT_SESSION"));
    }

    @Test
    void 내_다른_기기는_로그아웃되고_다른_기기_모두는_지금_기기만_남긴다() {
        when(refreshTokenMapper.findById(2L)).thenReturn(token(2, 7, "other-device"));
        loginSessionService.logout(7L, 2L, "this-device");
        verify(refreshTokenMapper).deleteById(2L);

        when(refreshTokenMapper.deleteOthers(7L, "this-device")).thenReturn(3);
        assertThat(loginSessionService.logoutOthers(7L, "this-device")).isEqualTo(3);
    }

    @Test
    void 기기_이름은_브라우저와_운영체제만() {
        assertThat(ClientDevice.describe("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"))
                .isEqualTo("Chrome · Windows");
        assertThat(ClientDevice.describe("Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/141.0 Safari/537.36 Edg/141.0"))
                .isEqualTo("Edge · Windows");
        assertThat(ClientDevice.describe("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1"))
                .isEqualTo("Safari · iOS");
        assertThat(ClientDevice.describe("Mozilla/5.0 (Linux; Android 15; SM-S921N) AppleWebKit/537.36 SamsungBrowser/27.0 Chrome/125.0 Mobile Safari/537.36"))
                .isEqualTo("Samsung Internet · Android");
        assertThat(ClientDevice.describe(null)).isNull();
    }
}
