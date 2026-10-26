package com.kh.back.admin.service;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.admin.mapper.AdminMemberMapper;
import com.kh.back.auth.mapper.RefreshTokenMapper;
import com.kh.back.auth.service.LoginAttemptLimiter;
import com.kh.back.common.exception.ApiException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

// 7단계: 총관리자의 관리자 권한 주기 · 빼기 규칙
@ExtendWith(MockitoExtension.class)
class AdminRoleChangeTests {

    @Mock AdminMemberMapper adminMemberMapper;
    @Mock LoginAttemptLimiter loginAttemptLimiter;
    @Mock RefreshTokenMapper refreshTokenMapper;
    @InjectMocks AdminMemberServiceImpl service;

    private static final Long SUPER_ADMIN_ID = 1L;

    @Test
    void 일반_회원을_관리자로_지정하면_다시_로그인해야_한다() {
        when(adminMemberMapper.findRole(7L)).thenReturn("USER");

        service.changeRole(SUPER_ADMIN_ID, 7L, "ADMIN");

        verify(adminMemberMapper).updateRole(7L, "ADMIN");
        verify(refreshTokenMapper).deleteByUserId(7L); // 로그인된 기기 모두 로그아웃 → 다시 로그인하면 새 권한
    }

    @Test
    void 자기_자신의_권한은_못_바꾼다() {
        assertThatThrownBy(() -> service.changeRole(SUPER_ADMIN_ID, SUPER_ADMIN_ID, "USER"))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("SELF_ROLE_CHANGE"));
        verify(adminMemberMapper, never()).updateRole(anyLong(), any());
    }

    @Test
    void 총관리자의_권한은_못_바꾼다() {
        when(adminMemberMapper.findRole(2L)).thenReturn("SUPER_ADMIN");

        assertThatThrownBy(() -> service.changeRole(SUPER_ADMIN_ID, 2L, "USER"))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("SUPER_ADMIN_PROTECTED"));
        verify(adminMemberMapper, never()).updateRole(anyLong(), any());
    }

    @Test
    void 없는_회원이면_404() {
        assertThatThrownBy(() -> service.changeRole(SUPER_ADMIN_ID, 99L, "ADMIN"))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("MEMBER_NOT_FOUND"));
    }

    @Test
    void 이미_그_권한이면_아무것도_하지_않는다() {
        when(adminMemberMapper.findRole(7L)).thenReturn("ADMIN");

        service.changeRole(SUPER_ADMIN_ID, 7L, "ADMIN");

        verify(adminMemberMapper, never()).updateRole(anyLong(), any());
        verify(refreshTokenMapper, never()).deleteByUserId(anyLong());
    }
}
