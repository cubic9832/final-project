package com.kh.back.admin.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.kh.back.admin.mapper.AdminMemberMapper;
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.mapper.MemberMapper;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.security.crypto.password.PasswordEncoder;

// 7단계: 총관리자 계정 시드 — 환경변수가 있을 때만 만들고, 이미 있으면 권한만 올린다
class AdminAccountSeederTests {

    private final MemberMapper memberMapper = mock(MemberMapper.class);
    private final AdminMemberMapper adminMemberMapper = mock(AdminMemberMapper.class);
    private final PasswordEncoder passwordEncoder = mock(PasswordEncoder.class);

    private AdminAccountSeeder seeder(String email, String password) {
        return new AdminAccountSeeder(memberMapper, adminMemberMapper, passwordEncoder, email, password);
    }

    @Test
    void 환경변수가_없으면_아무것도_하지_않는다() {
        seeder("", "").seed();
        verifyNoInteractions(memberMapper, adminMemberMapper);
    }

    @Test
    void 없는_이메일이면_총관리자를_만든다() {
        when(passwordEncoder.encode(any())).thenReturn("hashed");

        seeder(" Boss@Example.com ", "Credit#Seed27").seed();

        ArgumentCaptor<MemberDto> saved = ArgumentCaptor.forClass(MemberDto.class);
        verify(memberMapper).insert(saved.capture());
        assertThat(saved.getValue().getEmail()).isEqualTo("boss@example.com");
        assertThat(saved.getValue().getRole()).isEqualTo("SUPER_ADMIN");
        assertThat(saved.getValue().getPasswordHash()).isEqualTo("hashed");
    }

    @Test
    void 이미_가입한_회원이면_권한만_올린다() {
        MemberDto member = new MemberDto();
        member.setId(5L);
        member.setRole("USER");
        when(memberMapper.findByEmail("boss@example.com")).thenReturn(member);

        seeder("boss@example.com", "").seed();

        verify(adminMemberMapper).updateRole(5L, "SUPER_ADMIN");
        verify(memberMapper, never()).insert(any());
    }

    @Test
    void 비밀번호가_규칙에_맞지_않으면_만들지_않는다() {
        seeder("boss@example.com", "1234").seed();
        verify(memberMapper, never()).insert(any());
        verify(adminMemberMapper, never()).updateRole(anyLong(), any());
    }
}
