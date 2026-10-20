package com.kh.back.auth;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

/**
 * 마이페이지 비밀번호 변경에서 현재 비밀번호를 틀린 횟수 (보완 2 추가 · 10-20).
 * 로그인한 채로 자리를 비운 사이 다른 사람이 현재 비밀번호를 계속 맞춰 보는 것을 막는다.
 * 회원 번호별로 서버 메모리에 센다 (LoginAttemptLimiter 와 같은 방식, 서버를 다시 켜면 초기화).
 */
@Component
public class PasswordChangeLimiter {

    static final int LOGOUT_LIMIT = 5; // 5번 틀리면 로그아웃

    private final Map<Long, Integer> failures = new ConcurrentHashMap<>();

    /** 한 번 틀렸다고 기록하고, 지금까지 틀린 횟수를 돌려준다 */
    public int recordFailure(Long userId) {
        return failures.merge(userId, 1, Integer::sum);
    }

    /** 바꾸기에 성공했거나 로그아웃시켰으면 다시 0부터 */
    public void reset(Long userId) {
        failures.remove(userId);
    }
}
