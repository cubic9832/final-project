package com.kh.back.member.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.ArgumentMatchers.notNull;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.dto.UserAgreementDto;
import com.kh.back.member.mapper.MemberMapper;
import com.kh.back.member.mapper.UserAgreementMapper;
import java.time.LocalDateTime;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

// 보완 9: 이메일 알림 범위 — ALL 이면 추천 업데이트 수신 동의 시각을 남기고, 다른 범위면 지운다
@ExtendWith(MockitoExtension.class)
class MemberNotificationTests {

    @Mock MemberMapper memberMapper;
    @Mock UserAgreementMapper userAgreementMapper;
    @InjectMocks MemberServiceImpl memberService;

    @BeforeEach
    void setUp() {
        MemberDto member = new MemberDto();
        member.setId(7L);
        org.mockito.Mockito.lenient().when(memberMapper.findById(7L)).thenReturn(member); // 알림 바꾸기 테스트에서만 쓴다
    }

    @Test
    void 기록이_없는_회원은_기본값_IMPORTANT() {
        assertThat(memberService.getAgreement(7L).getEmailNotification()).isEqualTo("IMPORTANT");
    }

    @Test
    void ALL_로_바꾸면_수신_동의_시각을_남긴다() {
        memberService.updateNotification(7L, "ALL");
        verify(userAgreementMapper).upsertNotification(eq(7L), eq("ALL"), notNull());
    }

    @Test
    void 다른_범위로_바꾸면_수신_동의_시각을_지운다() {
        UserAgreementDto saved = UserAgreementDto.atSignup(7L, true, LocalDateTime.of(2026, 10, 26, 10, 0));
        when(userAgreementMapper.findByUserId(7L)).thenReturn(saved);

        memberService.updateNotification(7L, "NONE");

        verify(userAgreementMapper).upsertNotification(eq(7L), eq("NONE"), isNull());
    }

    @Test
    void 이미_ALL_이면_처음_동의_시각을_유지한다() {
        LocalDateTime first = LocalDateTime.of(2026, 10, 1, 9, 0);
        UserAgreementDto saved = UserAgreementDto.atSignup(7L, true, first);
        when(userAgreementMapper.findByUserId(7L)).thenReturn(saved);

        memberService.updateNotification(7L, "ALL");

        verify(userAgreementMapper).upsertNotification(7L, "ALL", first);
    }

    @Test
    void 가입할_때_선택_동의에_따라_알림이_정해진다() {
        LocalDateTime now = LocalDateTime.now();
        assertThat(UserAgreementDto.atSignup(1L, true, now).getEmailNotification()).isEqualTo("ALL");
        assertThat(UserAgreementDto.atSignup(1L, false, now).getEmailNotification()).isEqualTo("IMPORTANT");
        assertThat(UserAgreementDto.atSignup(1L, false, now).getUpdatesAgreedAt()).isNull();
        assertThat(UserAgreementDto.atSignup(1L, false, now).getTermsAgreedAt()).isEqualTo(now);
    }
}
