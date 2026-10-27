package com.kh.back.admin.service;

import com.kh.back.admin.mapper.AdminMemberMapper;
import com.kh.back.auth.service.PasswordPolicy;
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.mapper.MemberMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * 7단계: 총관리자 계정 시드 (서버가 켜질 때 한 번).
 * 각자 컴퓨터 DB 에는 관리자가 없어서, 환경변수 ADMIN_SEED_EMAIL · ADMIN_SEED_PASSWORD 를 넣고 서버를 켜면
 * 그 계정을 총관리자(SUPER_ADMIN)로 만든다. 이미 가입한 이메일이면 권한만 총관리자로 올린다 (비밀번호는 그대로).
 * 비밀번호는 코드 · git 에 넣지 않는다. 환경변수가 없으면 아무것도 하지 않는다 → 배포 서버에 계정이 몰래 생기지 않는다.
 */
@Slf4j
@Component
public class AdminAccountSeeder {

    static final String SEED_NICKNAME = "총관리자";
    // 회원가입(SignupRequest)과 같은 길이 · 문자 종류 규칙: 8~20자, 영문 · 숫자 · 특수문자 포함, 공백 없음
    private static final String PASSWORD_FORMAT = "^(?=.*[A-Za-z])(?=.*\\d)(?=.*[^A-Za-z0-9])\\S{8,20}$";

    private final MemberMapper memberMapper;
    private final AdminMemberMapper adminMemberMapper;
    private final PasswordEncoder passwordEncoder;
    private final String email;
    private final String password;

    public AdminAccountSeeder(MemberMapper memberMapper, AdminMemberMapper adminMemberMapper, PasswordEncoder passwordEncoder,
                              @Value("${admin.seed.email:}") String email,
                              @Value("${admin.seed.password:}") String password) {
        this.memberMapper = memberMapper;
        this.adminMemberMapper = adminMemberMapper;
        this.passwordEncoder = passwordEncoder;
        this.email = email.trim().toLowerCase(); // 회원가입 · 로그인과 같은 이메일 정리 규칙
        this.password = password;
    }

    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void seed() {
        if (email.isBlank()) {
            return; // 환경변수가 없으면 시드하지 않는다 (기본)
        }
        MemberDto existing = memberMapper.findByEmail(email);
        if (existing != null) {
            // 이미 가입한 회원: 권한만 총관리자로 (로그 · 비밀번호는 찍지 않는다)
            if (!"SUPER_ADMIN".equals(existing.getRole())) {
                adminMemberMapper.updateRole(existing.getId(), "SUPER_ADMIN");
                log.info("admin seed: existing member {} promoted to SUPER_ADMIN", existing.getId());
            }
            return;
        }
        if (password.isBlank()) {
            log.warn("admin seed skipped: ADMIN_SEED_PASSWORD is empty");
            return;
        }
        // 회원가입과 같은 비밀번호 규칙 (약한 비밀번호로 총관리자가 생기지 않게)
        String violation = PasswordPolicy.check(password, email);
        if (!password.matches(PASSWORD_FORMAT) || violation != null) {
            log.warn("admin seed skipped: password does not meet the password policy");
            return;
        }
        MemberDto member = new MemberDto();
        member.setEmail(email);
        member.setPasswordHash(passwordEncoder.encode(password));
        member.setNickName(memberMapper.countByNickName(SEED_NICKNAME) == 0 ? SEED_NICKNAME : SEED_NICKNAME + System.currentTimeMillis() % 10000);
        member.setRole("SUPER_ADMIN");
        memberMapper.insert(member);
        log.info("admin seed: SUPER_ADMIN account created (id {})", member.getId());
    }
}
