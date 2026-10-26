package com.kh.back.auth.service;

import com.kh.back.common.exception.ApiException;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import java.time.Duration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/**
 * 보완 8: 화면이 구글에서 받은 ID 토큰이 진짜인지 구글에 물어보고, 구글 사용자 정보를 꺼낸다.
 * 이 방식은 Client ID 만 필요하다 (Client Secret 없음 → git 에 숨길 비밀 키가 없다).
 * Client ID 는 application.yml 의 google.client-id (환경변수 GOOGLE_CLIENT_ID).
 * https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
 */
@Slf4j
@Component
public class GoogleTokenVerifier {

    private static final String TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo?id_token={token}";

    private final String clientId;
    // 10-22: 구글이 응답하지 않을 때 로그인 요청이 끝없이 기다리지 않도록 시간 제한 (연결 3초 · 응답 5초)
    private final RestClient restClient = RestClient.builder().requestFactory(timeoutFactory()).build();

    private static SimpleClientHttpRequestFactory timeoutFactory() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(3));
        factory.setReadTimeout(Duration.ofSeconds(5));
        return factory;
    }

    public GoogleTokenVerifier(@Value("${google.client-id:}") String clientId) {
        this.clientId = clientId;
    }

    // 구글이 확인해 준 사용자. sub = 구글 고유 번호 (이메일이 바뀌어도 그대로)
    public record GoogleUser(String sub, String email, String name) {
    }

    public GoogleUser verify(String idToken) {
        if (clientId.isBlank()) {
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "GOOGLE_NOT_CONFIGURED",
                    "구글 로그인이 아직 설정되지 않았습니다. (GOOGLE_CLIENT_ID)");
        }
        Map<?, ?> info;
        try {
            info = restClient.get().uri(TOKEN_INFO_URL, idToken).retrieve().body(Map.class);
        } catch (RestClientException e) {
            log.warn("구글 토큰 확인 실패: {}", e.getMessage());
            throw invalid();
        }
        // 우리 서비스용으로 발급된 토큰인지(aud), 구글이 발급했는지(iss), 이메일이 확인된 계정인지
        if (info == null
                || !clientId.equals(info.get("aud"))
                || !(("accounts.google.com".equals(info.get("iss"))) || "https://accounts.google.com".equals(info.get("iss")))
                || !"true".equals(String.valueOf(info.get("email_verified")))
                || info.get("sub") == null || info.get("email") == null) {
            throw invalid();
        }
        Object name = info.get("name");
        return new GoogleUser(String.valueOf(info.get("sub")),
                String.valueOf(info.get("email")).trim().toLowerCase(),
                name == null ? "" : String.valueOf(name));
    }

    private ApiException invalid() {
        return new ApiException(HttpStatus.UNAUTHORIZED, "GOOGLE_TOKEN_INVALID", "구글 로그인 정보를 확인하지 못했습니다. 다시 시도해 주세요.");
    }
}
