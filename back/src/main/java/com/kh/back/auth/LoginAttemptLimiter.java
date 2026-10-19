package com.kh.back.auth;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

/**
 * 보완 6: 로그인 실패 횟수 세기 → 일정 횟수를 넘으면 reCAPTCHA("로봇이 아닙니다")를 요구한다.
 *
 * - 서버 메모리에 둔다 (DB 없음). 서버를 다시 켜면 0 으로 돌아가지만 10분짜리 기록이라 문제없다
 * - 화면이 아니라 서버가 센다 → 새로고침으로 초기화할 수 없다
 * - 이메일별 3번: 한 계정의 비밀번호를 계속 맞혀 보는 공격
 *   접속 IP별 10번: 여러 이메일을 바꿔 가며 시도하는 공격 (같은 와이파이 사용자를 고려해 더 넉넉하게)
 * - 첫 실패부터 10분이 지나면 다시 0 부터 센다. 로그인에 성공하면 그 이메일의 기록을 지운다
 */
@Component
public class LoginAttemptLimiter {

    static final int EMAIL_LIMIT = 3;
    static final int IP_LIMIT = 10;
    static final Duration WINDOW = Duration.ofMinutes(10);

    // 키: "email:user@example.com" · "ip:127.0.0.1" (여러 요청이 동시에 써도 안전한 Map)
    private final Map<String, Attempt> attempts = new ConcurrentHashMap<>();

    private record Attempt(int count, Instant firstFailedAt) {
    }

    public boolean isCaptchaRequired(String email, String clientIp) {
        return count("email:" + email) >= EMAIL_LIMIT || count("ip:" + clientIp) >= IP_LIMIT;
    }

    public void recordFailure(String email, String clientIp) {
        increase("email:" + email);
        increase("ip:" + clientIp);
    }

    // 로그인 성공: 그 이메일의 실패 기록만 지운다 (IP 기록은 시간이 지나면 사라진다)
    public void reset(String email) {
        attempts.remove("email:" + email);
    }

    private int count(String key) {
        Attempt attempt = attempts.get(key);
        if (attempt == null) {
            return 0;
        }
        if (isExpired(attempt)) {
            attempts.remove(key, attempt);
            return 0;
        }
        return attempt.count();
    }

    // compute: 같은 키를 동시에 고쳐도 숫자가 빠지지 않게 한 번에 계산한다
    private void increase(String key) {
        attempts.compute(key, (k, attempt) -> attempt == null || isExpired(attempt)
                ? new Attempt(1, Instant.now())
                : new Attempt(attempt.count() + 1, attempt.firstFailedAt()));
    }

    private boolean isExpired(Attempt attempt) {
        return attempt.firstFailedAt().plus(WINDOW).isBefore(Instant.now());
    }
}
