package com.kh.back.member;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.common.exception.ApiException;
import java.time.LocalDate;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

// 6단계: 개인정보 수정 (만 18세 검사, 선택 항목 null = 그대로 · "" = 지우기, 구글 가입 회원은 행이 없어도 저장)
@ExtendWith(MockitoExtension.class)
class MemberProfileUpdateTests {

    @Mock MemberMapper memberMapper;
    @Mock UserProfileMapper userProfileMapper;
    @InjectMocks MemberServiceImpl memberService;

    @BeforeEach
    void setUp() {
        MemberDto member = new MemberDto();
        member.setId(7L);
        member.setEmail("g.user@gmail.com");
        member.setNickName("구글사용자");
        member.setRole("USER");
        member.setPasswordHash(MemberDto.SOCIAL_ONLY_PASSWORD);
        when(memberMapper.findById(7L)).thenReturn(member);
    }

    private ProfileUpdateRequest request(LocalDate birthDate) {
        ProfileUpdateRequest r = new ProfileUpdateRequest();
        r.setBirthDate(birthDate);
        r.setGender("NONE");
        r.setDrivingExperience("UNDER_1Y");
        r.setPurchaseTiming("WITHIN_6M");
        return r;
    }

    @Test
    void 만18세_미만_생년월일은_저장하지_않는다() {
        assertThatThrownBy(() -> memberService.updateProfile(7L, request(LocalDate.now().minusYears(17))))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("AGE_RESTRICTED"));
        verify(userProfileMapper, never()).upsert(any());
    }

    @Test
    void 구글_가입_회원도_처음_저장하면_행이_생긴다() {
        MemberResponse response = memberService.updateProfile(7L, request(LocalDate.of(1998, 5, 14)));

        ArgumentCaptor<UserProfileDto> saved = ArgumentCaptor.forClass(UserProfileDto.class);
        verify(userProfileMapper).upsert(saved.capture());
        assertThat(saved.getValue().getUserId()).isEqualTo(7L);
        assertThat(response.getBirthDate()).isEqualTo(LocalDate.of(1998, 5, 14));
        assertThat(response.getDrivingExperience()).isEqualTo("UNDER_1Y");
        assertThat(response.getPurchaseTiming()).isEqualTo("WITHIN_6M");
    }

    @Test
    void 전화번호는_null_이면_그대로_빈값이면_지운다() {
        UserProfileDto existing = new UserProfileDto();
        existing.setUserId(7L);
        existing.setPhone("01012345678");
        existing.setBirthDate(LocalDate.of(1998, 5, 14));
        when(userProfileMapper.findByUserId(7L)).thenReturn(existing);

        ProfileUpdateRequest keep = request(null);
        assertThat(memberService.updateProfile(7L, keep).getPhoneMasked()).isEqualTo("010-****-5678");

        ProfileUpdateRequest clear = request(null);
        clear.setPhone("");
        assertThat(memberService.updateProfile(7L, clear).getPhoneMasked()).isNull();
    }

    // 닉네임과 개인정보는 한 요청 · 한 트랜잭션: 닉네임이 거절되면 개인정보도 저장하지 않는다
    @Test
    void 닉네임이_중복이면_개인정보도_저장하지_않는다() {
        when(memberMapper.countByNickName("새닉네임")).thenReturn(1);
        ProfileUpdateRequest r = request(LocalDate.of(1998, 5, 14));
        r.setNickName("새닉네임");

        assertThatThrownBy(() -> memberService.updateProfile(7L, r))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("NICKNAME_DUPLICATED"));
        verify(userProfileMapper, never()).upsert(any());
    }

    // 생년월일 검사가 먼저라, 만 18세 미만이면 닉네임도 바꾸지 않는다
    @Test
    void 만18세_미만이면_닉네임도_바꾸지_않는다() {
        ProfileUpdateRequest r = request(LocalDate.now().minusYears(17));
        r.setNickName("새닉네임");

        assertThatThrownBy(() -> memberService.updateProfile(7L, r)).isInstanceOf(ApiException.class);
        verify(memberMapper, never()).updateNickName(any(), any());
    }

    @Test
    void 닉네임을_같이_보내면_함께_바뀐다() {
        ProfileUpdateRequest r = request(LocalDate.of(1998, 5, 14));
        r.setNickName("  새닉네임 ");

        assertThat(memberService.updateProfile(7L, r).getNickName()).isEqualTo("새닉네임");
        verify(memberMapper).updateNickName(7L, "새닉네임");
        verify(userProfileMapper).upsert(any());
    }
}
