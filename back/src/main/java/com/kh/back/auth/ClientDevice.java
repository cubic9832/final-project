package com.kh.back.auth;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

/**
 * 6단계: 로그인된 기기 목록에 보여 줄 기기 이름 (예: "Chrome · Windows").
 * 브라우저가 보내는 User-Agent 헤더에서 브라우저 · 운영체제 이름만 뽑는다. IP 주소는 저장하지 않는다 (개인정보).
 * User-Agent 는 사용자가 바꿀 수도 있어서, 보안 판단에는 쓰지 않고 "어느 기기인지 알아보기" 용도로만 쓴다.
 */
final class ClientDevice {

    private ClientDevice() {
    }

    // 지금 처리 중인 요청의 기기 이름. 요청 밖(테스트 등)이면 null
    static String current() {
        if (!(RequestContextHolder.getRequestAttributes() instanceof ServletRequestAttributes attributes)) {
            return null;
        }
        HttpServletRequest request = attributes.getRequest();
        return describe(request.getHeader("User-Agent"));
    }

    // 확인하는 순서가 중요하다: Edge · 웨일 · 삼성 인터넷의 User-Agent 에도 "Chrome" 이 들어 있고,
    // Chrome 에도 "Safari" 가, 안드로이드에도 "Linux" 가, 아이폰에도 "Mac OS X" 가 들어 있다
    static String describe(String userAgent) {
        if (userAgent == null || userAgent.isBlank()) {
            return null;
        }
        String browser;
        if (userAgent.contains("Edg/")) {
            browser = "Edge";
        } else if (userAgent.contains("Whale/")) {
            browser = "Whale";
        } else if (userAgent.contains("SamsungBrowser/")) {
            browser = "Samsung Internet";
        } else if (userAgent.contains("Chrome/") || userAgent.contains("CriOS/")) {
            browser = "Chrome";
        } else if (userAgent.contains("Firefox/") || userAgent.contains("FxiOS/")) {
            browser = "Firefox";
        } else if (userAgent.contains("Safari/")) {
            browser = "Safari";
        } else {
            browser = "기타 브라우저";
        }

        String os;
        if (userAgent.contains("Windows")) {
            os = "Windows";
        } else if (userAgent.contains("Android")) {
            os = "Android";
        } else if (userAgent.contains("iPhone") || userAgent.contains("iPad")) {
            os = "iOS";
        } else if (userAgent.contains("Mac OS X")) {
            os = "macOS";
        } else if (userAgent.contains("Linux")) {
            os = "Linux";
        } else {
            os = "기타";
        }
        return browser + " · " + os;
    }
}
