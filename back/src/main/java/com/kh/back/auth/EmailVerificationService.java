package com.kh.back.auth;

import com.kh.back.common.exception.ApiException;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 보완 7: 회원가입 전 이메일 인증
 * 1) [인증 코드 받기] → 6자리 코드를 만들어 해시로 저장하고 메일로 보낸다 (5분 유효)
 * 2) [확인] → 코드가 맞으면 인증 완료 표시 (30분 안에 가입해야 한다)
 * 3) 회원가입 → 인증 완료인지 확인하고, 가입이 끝나면 기록을 지운다
 *
 * 메일 폭탄 · 무작위 대입을 막는 제한: 60초 안에 다시 받기 X, 10분에 5번까지, 코드 5번 틀리면 다시 받아야 함
 */
@Service
@RequiredArgsConstructor
public class EmailVerificationService {

    static final Duration CODE_VALIDITY = Duration.ofMinutes(5);
    static final Duration RESEND_COOLDOWN = Duration.ofSeconds(60);
    static final Duration SEND_WINDOW = Duration.ofMinutes(10);
    static final int MAX_SENDS_PER_WINDOW = 5;
    static final int MAX_FAILED_ATTEMPTS = 5;
    static final Duration SIGNUP_DEADLINE = Duration.ofMinutes(30);

    private final SecureRandom random = new SecureRandom();
    private final EmailVerificationMapper verificationMapper;
    private final VerificationMailSender mailSender;
    private final PasswordEncoder passwordEncoder;

    // 코드를 만들어 보낸다. email 은 형식 · 중복 검사를 마친 소문자 이메일
    @Transactional
    public void sendCode(String email) {
        LocalDateTime now = LocalDateTime.now();
        EmailVerificationDto saved = verificationMapper.findByEmail(email);

        int sendCount = 1;
        LocalDateTime windowStartedAt = now;
        if (saved != null) {
            // 60초 안에는 다시 보내지 않는다
            long waitSeconds = Duration.between(now, saved.getLastSentAt().plus(RESEND_COOLDOWN)).getSeconds();
            if (waitSeconds > 0) {
                throw new ApiException(HttpStatus.TOO_MANY_REQUESTS, "VERIFICATION_COOLDOWN",
                        waitSeconds + "초 뒤에 다시 받을 수 있습니다.");
            }
            // 10분 구간 안에서 5번까지
            if (saved.getSendWindowStartedAt().plus(SEND_WINDOW).isAfter(now)) {
                if (saved.getSendCount() >= MAX_SENDS_PER_WINDOW) {
                    throw new ApiException(HttpStatus.TOO_MANY_REQUESTS, "VERIFICATION_LIMIT",
                            "인증 코드를 너무 많이 요청했습니다. 10분 뒤에 다시 시도해 주세요.");
                }
                sendCount = saved.getSendCount() + 1;
                windowStartedAt = saved.getSendWindowStartedAt();
            }
        }

        String code = String.format("%06d", random.nextInt(1_000_000)); // 000000 ~ 999999

        EmailVerificationDto verification = new EmailVerificationDto();
        verification.setEmail(email);
        verification.setCodeHash(passwordEncoder.encode(code)); // 원문은 저장하지 않는다
        verification.setExpiresAt(now.plus(CODE_VALIDITY));
        verification.setLastSentAt(now);
        verification.setSendWindowStartedAt(windowStartedAt);
        verification.setSendCount(sendCount);
        verificationMapper.save(verification);

        // 메일 발송이 실패하면 예외 → 트랜잭션이 취소되어 저장도 되돌아간다 (보내지 못한 코드가 남지 않게)
        mailSender.send(email, code);
    }

    // 코드 확인. 맞으면 인증 완료 표시
    // noRollbackFor: 틀린 횟수(+1)는 예외를 던져도 저장되어야 한다
    @Transactional(noRollbackFor = ApiException.class)
    public void confirmCode(String email, String code) {
        EmailVerificationDto saved = verificationMapper.findByEmail(email);
        if (saved == null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "VERIFICATION_NOT_FOUND", "[인증 코드 받기]를 먼저 눌러 주세요.");
        }
        if (saved.getFailedAttempts() >= MAX_FAILED_ATTEMPTS) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "VERIFICATION_ATTEMPTS_EXCEEDED",
                    "인증 코드를 5번 틀렸습니다. 코드를 다시 받아 주세요.");
        }
        if (saved.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "VERIFICATION_EXPIRED", "인증 코드가 만료되었습니다. 코드를 다시 받아 주세요.");
        }
        if (code == null || !passwordEncoder.matches(code.trim(), saved.getCodeHash())) {
            verificationMapper.increaseFailedAttempts(email);
            int left = MAX_FAILED_ATTEMPTS - saved.getFailedAttempts() - 1;
            throw new ApiException(HttpStatus.BAD_REQUEST, "VERIFICATION_CODE_MISMATCH", left > 0
                    ? "인증 코드가 올바르지 않습니다. (" + left + "번 남음)"
                    : "인증 코드를 5번 틀렸습니다. 코드를 다시 받아 주세요.");
        }
        verificationMapper.markVerified(email);
    }

    // 회원가입 직전: 인증을 마쳤고 30분이 지나지 않았는지
    public boolean isVerified(String email) {
        EmailVerificationDto saved = verificationMapper.findByEmail(email);
        return saved != null && saved.getVerifiedAt() != null
                && saved.getVerifiedAt().plus(SIGNUP_DEADLINE).isAfter(LocalDateTime.now());
    }

    // 회원가입이 끝나면 인증 기록을 지운다 (같은 트랜잭션)
    public void consume(String email) {
        verificationMapper.deleteByEmail(email);
    }

    public boolean isMailEnabled() {
        return mailSender.isMailEnabled();
    }
}
