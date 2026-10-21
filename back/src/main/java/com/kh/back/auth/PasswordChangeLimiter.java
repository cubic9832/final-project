package com.kh.back.auth;

import com.kh.back.common.exception.ApiException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

/**
 * 로그인한 상태에서 "현재 비밀번호 확인"을 틀린 횟수 (보완 2 추가 · 10-20, 보완 4 추가 · 10-21).
 * 비밀번호 변경과 회원 탈퇴가 같은 카운터를 쓴다 (둘 다 현재 비밀번호 확인 → 합쳐서 센다).
 * 로그인한 채로 자리를 비운 사이 다른 사람이 현재 비밀번호를 계속 맞춰 보는 것을 막는다.
 * 회원 번호별로 서버 메모리에 센다 (LoginAttemptLimiter 와 같은 방식, 서버를 다시 켜면 초기화).
 */
@Component
public class PasswordChangeLimiter {

    static final int LOGOUT_LIMIT = 5; // 5번 틀리면 로그아웃
    public static final String LOGOUT_CODE = "PASSWORD_CONFIRM_LOGOUT"; // 화면은 이 코드면 로그아웃 처리

    private final Map<Long, Integer> failures = new ConcurrentHashMap<>();

    /** 한 번 틀렸다고 기록하고, 지금까지 틀린 횟수를 돌려준다 */
    public int recordFailure(Long userId) {
        return failures.merge(userId, 1, Integer::sum);
    }

    /**
     * 현재 비밀번호를 틀렸을 때 던질 예외를 만든다.
     * 3번째부터 남은 횟수를 붙이고, 5번째면 횟수를 지우고 LOGOUT_CODE(401)를 돌려준다
     * → 받은 쪽(Service)이 refresh token 을 모두 지운 뒤 던진다
     */
    public ApiException mismatch(Long userId, String message) {
        int count = recordFailure(userId);
        if (count >= LOGOUT_LIMIT) {
            reset(userId);
            return new ApiException(HttpStatus.UNAUTHORIZED, LOGOUT_CODE,
                    "현재 비밀번호를 " + LOGOUT_LIMIT + "번 틀려 로그아웃되었습니다. 다시 로그인해 주세요.");
        }
        String warning = count >= 3 ? " (" + (LOGOUT_LIMIT - count) + "번 더 틀리면 로그아웃됩니다)" : "";
        return new ApiException(HttpStatus.BAD_REQUEST, "PASSWORD_MISMATCH", message + warning);
    }

    /** 성공했거나 로그아웃시켰으면 다시 0부터 */
    public void reset(Long userId) {
        failures.remove(userId);
    }
}
