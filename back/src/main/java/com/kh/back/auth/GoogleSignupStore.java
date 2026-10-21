package com.kh.back.auth;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

/**
 * 보완 8: 처음 구글로 들어온 사람의 "가입 대기" 정보 (서버 메모리, 10분).
 * 구글 확인은 끝났지만 닉네임 · 전화번호 · 생년월일 · 성별(보완 5 필수)을 아직 받지 않은 상태.
 * 화면에는 추측할 수 없는 가입 대기 번호(UUID)만 주고, 추가 정보와 함께 돌려받으면 꺼내서 가입시킨다.
 */
@Component
public class GoogleSignupStore {

    static final Duration VALIDITY = Duration.ofMinutes(10);

    public record Pending(String sub, String email, String name, Instant expiresAt) {
    }

    private final Map<String, Pending> pendings = new ConcurrentHashMap<>();

    public String save(GoogleTokenVerifier.GoogleUser user) {
        pendings.values().removeIf(p -> p.expiresAt().isBefore(Instant.now())); // 지난 것 정리
        String token = UUID.randomUUID().toString();
        pendings.put(token, new Pending(user.sub(), user.email(), user.name(), Instant.now().plus(VALIDITY)));
        return token;
    }

    // 확인만 한다 (지우지 않음). 없거나 10분이 지났으면 null
    // 10-22: 닉네임 중복 · 나이 오류 등으로 거절돼도 고쳐서 다시 낼 수 있게, 지우기는 가입이 성공한 뒤 remove 로
    public Pending peek(String token) {
        Pending pending = token == null ? null : pendings.get(token);
        return pending == null || pending.expiresAt().isBefore(Instant.now()) ? null : pending;
    }

    // 가입이 끝났으면 지운다 → 같은 번호로 다시 가입할 수 없다 (1회용)
    public void remove(String token) {
        if (token != null) {
            pendings.remove(token);
        }
    }
}
