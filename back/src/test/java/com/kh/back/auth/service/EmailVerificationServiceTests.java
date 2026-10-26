package com.kh.back.auth.service;

import com.kh.back.auth.dto.EmailVerificationDto;
import com.kh.back.auth.mapper.EmailVerificationMapper;

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

// 보완 7 추가: 하루 발송 상한(10-20) · 이미 인증한 이메일도 새 코드를 보냄(10-22, 증명 번호는 인증한 사람만 가짐)
@ExtendWith(MockitoExtension.class)
class EmailVerificationServiceTests {

    @Mock EmailVerificationMapper verificationMapper;
    @Mock VerificationMailSender mailSender;
    @Mock PasswordEncoder passwordEncoder;
    @InjectMocks EmailVerificationServiceImpl service;

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
    void 이미_인증한_이메일도_다시_받으면_새_코드를_보낸다() {
        ReflectionTestUtils.setField(service, "dailyLimit", 10);
        EmailVerificationDto saved = new EmailVerificationDto();
        saved.setEmail("a@example.com");
        saved.setVerifiedAt(LocalDateTime.now().minusMinutes(10));
        saved.setLastSentAt(LocalDateTime.now().minusMinutes(10));
        saved.setSendWindowStartedAt(LocalDateTime.now().minusMinutes(10));
        saved.setSendCount(1);
        when(verificationMapper.findByEmail("a@example.com")).thenReturn(saved);

        service.sendCode("a@example.com");
        verify(mailSender).send(org.mockito.ArgumentMatchers.eq("a@example.com"), any());
    }
}
