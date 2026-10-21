package com.kh.back.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.common.exception.ApiException;
import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;

// 보완 7 추가(10-20): 하루 발송 상한 · 이미 인증된 이메일은 다시 보내지 않음
@ExtendWith(MockitoExtension.class)
class EmailVerificationServiceTests {

    @Mock EmailVerificationMapper verificationMapper;
    @Mock VerificationMailSender mailSender;
    @Mock PasswordEncoder passwordEncoder;
    @InjectMocks EmailVerificationService service;

    @Test
    void 하루_상한을_넘으면_보내지_않는다() {
        ReflectionTestUtils.setField(service, "dailyLimit", 2);

        service.sendCode("a@example.com");
        service.sendCode("b@example.com");

        assertThatThrownBy(() -> service.sendCode("c@example.com"))
                .isInstanceOf(ApiException.class).hasMessageContaining("오늘은 인증 메일 요청이 많아");
        verify(mailSender, never()).send(org.mockito.ArgumentMatchers.eq("c@example.com"), any());
    }

    @Test
    void 인증한지_30분이_안된_이메일은_다시_보내지_않는다() {
        EmailVerificationDto saved = new EmailVerificationDto();
        saved.setEmail("a@example.com");
        saved.setVerifiedAt(LocalDateTime.now().minusMinutes(10));
        when(verificationMapper.findByEmail("a@example.com")).thenReturn(saved);

        assertThat(service.sendCode("a@example.com")).isTrue();
        verify(mailSender, never()).send(any(), any());
    }
}
