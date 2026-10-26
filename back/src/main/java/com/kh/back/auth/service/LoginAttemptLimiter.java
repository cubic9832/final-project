package com.kh.back.auth.service;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

/**
 * 보완 6: 로그인 실패 횟수 세기
 * - 3번째 실패부터 reCAPTCHA("로봇이 아닙니다")를 요구한다
 * - 5번째 실패하면 10분 동안 잠근다 (잠긴 동안에는 맞는 비밀번호여도 로그인할 수 없다)
 *
 * - 서버 메모리에 둔다 (DB 없음). 서버를 다시 켜면 0 으로 돌아가지만 10분짜리 기록이라 문제없다
 * - 화면이 아니라 서버가 센다 → 새로고침으로 초기화할 수 없다
 * - 이메일별로 센다 (가입하지 않은 이메일도 똑같이 → 어떤 이메일이 가입됐는지 드러나지 않는다)
 *   접속 IP 로는 세지 않는다 — 같은 와이파이 · 같은 프록시 뒤의 사용자가 서로 영향을 받기 때문
 * - 첫 실패부터 10분이 지나면 다시 0 부터 센다. 잠겼으면 잠금이 풀릴 때 0 부터. 로그인 · 회원가입에 성공하면 기록을 지운다
 * - 기록이 1,000개를 넘으면 기한 지난 기록을 한꺼번에 지운다 (메모리가 계속 늘지 않게)
 */
@Component
public class LoginAttemptLimiter {

    static final int CAPTCHA_LIMIT = 3;
    static final int LOCK_LIMIT = 5;
    static final Duration WINDOW = Duration.ofMinutes(10);
    static final Duration LOCK_DURATION = Duration.ofMinutes(10);
    // 기록이 이만큼 넘게 쌓이면 기한 지난 기록을 한꺼번에 지운다 (보완 6 추가: 메모리 정리)
    static final int CLEANUP_THRESHOLD = 1000;

    // 키: 이메일 (여러 요청이 동시에 써도 안전한 Map)
    private final Map<String, Attempt> attempts = new ConcurrentHashMap<>();

    // lockedUntil: 잠금이 풀리는 시각 (잠기지 않았으면 null)
    private record Attempt(int count, Instant firstFailedAt, Instant lockedUntil) {
    }

    public boolean isCaptchaRequired(String email) {
        Attempt attempt = current(email);
        return attempt != null && attempt.count() >= CAPTCHA_LIMIT;
    }

    // 지금까지 실패한 횟수 (기한이 지났으면 0)
    public int failureCount(String email) {
        Attempt attempt = current(email);
        return attempt == null ? 0 : attempt.count();
    }

    // 잠금이 풀릴 때까지 남은 분 (올림). 잠기지 않았으면 0
    public long lockedMinutesLeft(String email) {
        Attempt attempt = current(email);
        if (attempt == null || attempt.lockedUntil() == null) {
            return 0;
        }
        long seconds = Duration.between(Instant.now(), attempt.lockedUntil()).getSeconds();
        return Math.max(1, (seconds + 59) / 60);
    }

    // compute: 같은 이메일로 동시에 실패해도 숫자가 빠지지 않게 한 번에 계산한다
    public void recordFailure(String email) {
        cleanUpIfLarge();
        attempts.compute(email, (key, attempt) -> {
            if (attempt == null || isExpired(attempt)) {
                return new Attempt(1, Instant.now(), null);
            }
            int count = attempt.count() + 1;
            Instant lockedUntil = count >= LOCK_LIMIT ? Instant.now().plus(LOCK_DURATION) : null;
            return new Attempt(count, attempt.firstFailedAt(), lockedUntil);
        });
    }

    // 로그인 성공: 그 이메일의 실패 기록을 지운다
    public void reset(String email) {
        attempts.remove(email);
    }

    // 보완 6 추가: 기록은 그 이메일로 다시 로그인할 때만 지워져서, 없는 이메일 수천 개로 시도하면 계속 쌓인다
    // → 기록이 많아지면 기한(10분 · 잠금 시간)이 지난 것을 모두 지운다
    private void cleanUpIfLarge() {
        if (attempts.size() > CLEANUP_THRESHOLD) {
            attempts.values().removeIf(this::isExpired);
        }
    }

    // 기한이 지난 기록은 지우고 null 을 돌려준다
    private Attempt current(String email) {
        Attempt attempt = attempts.get(email);
        if (attempt != null && isExpired(attempt)) {
            attempts.remove(email, attempt);
            return null;
        }
        return attempt;
    }

    private boolean isExpired(Attempt attempt) {
        Instant now = Instant.now();
        if (attempt.lockedUntil() != null) {
            return now.isAfter(attempt.lockedUntil()); // 잠겼으면 잠금이 풀린 뒤 0 부터
        }
        return attempt.firstFailedAt().plus(WINDOW).isBefore(now);
    }
}
