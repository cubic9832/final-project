package com.kh.back.auth.service;

import com.kh.back.auth.dto.LoginSessionResponse;
import java.util.List;

/**
 * 6단계: 로그인된 기기 보기 · 기기별 로그아웃 · 다른 기기 모두 로그아웃.
 * 로그인된 기기 = 기한이 남은 refresh token 1행. 구현은 LoginSessionServiceImpl.
 */
public interface LoginSessionService {

    // 내 로그인된 기기 목록. currentToken(쿠키)과 같은 행에 "현재 기기" 표시
    List<LoginSessionResponse> list(Long userId, String currentToken);

    // 기기 하나 로그아웃. 없으면 404, 남의 기기면 403, 지금 기기면 400
    void logout(Long userId, Long sessionId, String currentToken);

    // 다른 기기 모두 로그아웃 — 지금 기기만 남긴다. 지운 기기 수를 돌려준다
    int logoutOthers(Long userId, String currentToken);
}
