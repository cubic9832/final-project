package com.kh.back.auth;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

/**
 * 이메일 인증을 마친 "그 사람"에게만 주는 일회용 증명 (보완 7 추가 · 10-22).
 * 코드 확인에 성공하면 추측할 수 없는 번호(UUID)를 화면에 주고, 회원가입 · 비밀번호 재설정은 이 번호가 있어야 통과한다.
 * 이전에는 "이 이메일이 30분 안에 인증됨"만 봐서, 인증 직후 다른 사람이 같은 이메일로 가입 · 비밀번호 변경을 보낼 수 있었다.
 * 서버 메모리에 30분 보관하고 한 번 쓰면 지운다 (GoogleSignupStore 와 같은 방식, 서버를 다시 켜면 다시 인증).
 */
@Component
public class EmailVerificationProofStore {

    static final int CLEANUP_THRESHOLD = 1000; // 이만큼 쌓이면 기한 지난 것부터 정리

    private record Proof(String email, Instant expiresAt) {
    }

    private final Map<String, Proof> proofs = new ConcurrentHashMap<>();

    /** 인증을 마친 이메일에 증명 번호를 만들어 준다 (인증 유효 시간과 같은 30분) */
    public String issue(String email) {
        if (proofs.size() >= CLEANUP_THRESHOLD) {
            Instant now = Instant.now();
            proofs.values().removeIf(p -> p.expiresAt().isBefore(now));
        }
        String token = UUID.randomUUID().toString();
        proofs.put(token, new Proof(email, Instant.now().plus(EmailVerificationService.SIGNUP_DEADLINE)));
        return token;
    }

    /** 이 이메일에 발급한, 아직 기한이 남은 번호인지 (지우지 않는다 — 가입이 끝난 뒤 remove) */
    public boolean isValid(String token, String email) {
        Proof proof = token == null ? null : proofs.get(token);
        return proof != null && proof.email().equals(email) && proof.expiresAt().isAfter(Instant.now());
    }

    /** 한 번 썼으면 지운다 (일회용) */
    public void remove(String token) {
        if (token != null) {
            proofs.remove(token);
        }
    }
}
