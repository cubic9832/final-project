package com.kh.back.auth.service;

import com.kh.back.common.exception.ApiException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import java.io.UnsupportedEncodingException;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Component;

/**
 * 보완 7: 인증 코드 메일 보내기.
 * 메일 계정은 application.yml 의 spring.mail.username · password (환경변수 MAIL_USERNAME · MAIL_PASSWORD) — 코드 · git 에 넣지 않는다.
 * 계정이 비어 있으면 메일 대신 서버 로그에 코드를 찍는다 (개발 모드 — 키 없이도 조원이 테스트할 수 있게).
 */
@Slf4j
@Component
public class VerificationMailSender {

    private static final String SENDER_NAME = "CreditCompass";

    private final JavaMailSender mailSender;
    private final String username;
    private final String password;

    public VerificationMailSender(JavaMailSender mailSender,
                                  @Value("${spring.mail.username:}") String username,
                                  @Value("${spring.mail.password:}") String password) {
        this.mailSender = mailSender;
        this.username = username;
        this.password = password;
    }

    // 실제 메일을 보내는지 (false 면 개발 모드: 서버 로그)
    public boolean isMailEnabled() {
        return !username.isBlank() && !password.isBlank();
    }

    // 실패하면 503 MAIL_SEND_FAILED (계정 · 앱 비밀번호가 틀렸거나 메일 서버에 연결하지 못함)
    public void send(String email, String code) {
        if (!isMailEnabled()) {
            // 콘솔 인코딩에 따라 한글이 깨질 수 있어 로그는 영문 · 숫자로만 찍는다
            log.info("[DEV-MAIL] email verification code={} to={} (MAIL_USERNAME/MAIL_PASSWORD not set)", code, email);
            return;
        }
        // 보낸 사람 이름을 따로(UTF-8) 넣는다 — "이름 <주소>" 문자열로만 넣으면 메일 앱이 계정 이름(아이디)을 보여 줄 수 있다
        MimeMessage message = mailSender.createMimeMessage();
        try {
            MimeMessageHelper helper = new MimeMessageHelper(message, false, "UTF-8");
            helper.setFrom(username, SENDER_NAME);
            helper.setTo(email);
            helper.setSubject("[" + SENDER_NAME + "] 이메일 인증 코드");
            helper.setText("""
                    %s 이메일 인증 코드입니다.

                    인증 코드: %s

                    화면에 5분 안에 입력해 주세요.
                    본인이 요청하지 않았다면 이 메일은 무시해 주세요.
                    """.formatted(SENDER_NAME, code));
        } catch (MessagingException | UnsupportedEncodingException e) {
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "MAIL_SEND_FAILED",
                    "인증 메일을 보내지 못했습니다. 잠시 후 다시 시도해 주세요.");
        }
        try {
            mailSender.send(message);
        } catch (MailException e) {
            log.warn("인증 메일 발송 실패: {}", e.getMessage());
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "MAIL_SEND_FAILED",
                    "인증 메일을 보내지 못했습니다. 잠시 후 다시 시도해 주세요.");
        }
    }
}
