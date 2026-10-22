package com.kh.back.auth;

import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/**
 * 보완 6: 화면에서 받은 reCAPTCHA 토큰이 진짜인지 구글에 물어본다.
 * 비밀 키는 application.yml 의 recaptcha.secret-key (환경변수 RECAPTCHA_SECRET_KEY) — 코드 · git 에 실제 키를 넣지 않는다.
 * https://developers.google.com/recaptcha/docs/verify
 */
@Slf4j
@Component
public class RecaptchaVerifier {

    private static final String VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify";

    private final String secretKey;
    private final RestClient restClient = RestClient.create();

    public RecaptchaVerifier(@Value("${recaptcha.secret-key}") String secretKey) {
        this.secretKey = secretKey;
    }

    // 구글 응답 { success: true/false, ... } 의 success 를 돌려준다. 구글에 연결하지 못해도 false (통과시키지 않는다)
    public boolean verify(String token, String clientIp) {
        MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
        form.add("secret", secretKey);
        form.add("response", token);
        form.add("remoteip", clientIp);
        try {
            Map<?, ?> body = restClient.post()
                    .uri(VERIFY_URL)
                    .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                    .body(form)
                    .retrieve()
                    .body(Map.class);
            return body != null && Boolean.TRUE.equals(body.get("success"));
        } catch (RestClientException e) {
            log.warn("reCAPTCHA 확인 요청 실패: {}", e.getMessage());
            return false;
        }
    }
}
