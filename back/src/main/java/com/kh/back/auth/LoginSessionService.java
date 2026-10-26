package com.kh.back.auth;

import com.kh.back.common.exception.ApiException;
import java.time.LocalDateTime;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 6단계: 로그인된 기기 보기 · 기기별 로그아웃 · 다른 기기 모두 로그아웃.
 * 로그인된 기기 = 기한이 남은 refresh token. 지우면 그 기기는 로그인을 이어 갈 수 없다.
 * 다만 그 기기에 이미 발급된 access token(JWT)은 DB 를 보지 않아 최대 30분 동안 남는다 → 화면에서 안내한다.
 */
@Service
@RequiredArgsConstructor
public class LoginSessionService {

    private final RefreshTokenMapper refreshTokenMapper;

    // 내 로그인된 기기 목록. currentToken(쿠키)과 같은 행에 "현재 기기" 표시
    @Transactional(readOnly = true)
    public List<LoginSessionResponse> list(Long userId, String currentToken) {
        return refreshTokenMapper.findActiveByUserId(userId, LocalDateTime.now()).stream()
                .map(token -> LoginSessionResponse.from(token, currentToken))
                .toList();
    }

    // 기기 하나 로그아웃
    // 스터디(CRUD) 와 같은 규칙: 없는 번호면 404, 남의 기기면 403 (로그인은 했지만 권한이 없음)
    @Transactional
    public void logout(Long userId, Long sessionId, String currentToken) {
        RefreshTokenDto token = refreshTokenMapper.findById(sessionId);
        if (token == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "SESSION_NOT_FOUND", "이미 로그아웃된 기기입니다.");
        }
        if (!token.getUserId().equals(userId)) {
            throw new ApiException(HttpStatus.FORBIDDEN, "SESSION_FORBIDDEN", "내 기기만 로그아웃할 수 있습니다.");
        }
        if (token.getToken().equals(currentToken)) {
            // 지금 기기는 쿠키 삭제까지 해야 해서 헤더의 [로그아웃] 을 쓰게 한다
            throw new ApiException(HttpStatus.BAD_REQUEST, "CURRENT_SESSION", "지금 기기는 화면 위의 [로그아웃]을 이용해 주세요.");
        }
        refreshTokenMapper.deleteById(sessionId);
    }

    // 다른 기기 모두 로그아웃 — 지금 기기만 남긴다. 지운 기기 수를 돌려준다
    @Transactional
    public int logoutOthers(Long userId, String currentToken) {
        if (currentToken == null || currentToken.isBlank()) {
            // 쿠키가 없으면 어느 기기가 "지금" 인지 알 수 없다 → 지우지 않는다
            throw new ApiException(HttpStatus.BAD_REQUEST, "CURRENT_SESSION_UNKNOWN", "로그인 정보를 확인하지 못했습니다. 다시 로그인해 주세요.");
        }
        return refreshTokenMapper.deleteOthers(userId, currentToken);
    }
}
