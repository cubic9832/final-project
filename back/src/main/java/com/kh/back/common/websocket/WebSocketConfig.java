package com.kh.back.common.websocket;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * 8단계: WebSocket + STOMP 설정 (1:1 상담 채팅). 강의 샘플 step4 와 같은 구조.
 * 화면 → 서버는 /app, 서버 → 구독자는 /topic, 한 사람에게는 /user/queue 로 보낸다.
 */
@Configuration
@EnableWebSocketMessageBroker   // STOMP 메시지 처리를 켠다
@RequiredArgsConstructor
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    private final StompAuthInterceptor stompAuthInterceptor;
    private final StompErrorHandler stompErrorHandler;

    // ① 연결 주소: ws://localhost:5173/ws (Vite 가 8080 으로 넘긴다)
    // 허용 출처: 내 PC(localhost) · 같은 와이파이의 공용 서버(192.168.x.x) 개발 화면 — 배포하면 배포 주소로 바꾼다
    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("http://localhost:*", "http://127.0.0.1:*", "http://192.168.*.*:*");
        registry.setErrorHandler(stompErrorHandler);
    }

    // ② 주소 규칙
    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.setApplicationDestinationPrefixes("/app");   // 화면 → 서버 (@MessageMapping)
        registry.enableSimpleBroker("/topic", "/queue");      // 서버 → 구독자 (Spring 안의 작은 우체국)
        registry.setUserDestinationPrefix("/user");           // 한 사람에게 (/user/queue/...)
    }

    // ③ 화면에서 들어오는 모든 STOMP 메시지가 이 인터셉터를 먼저 거친다 (REST 의 JwtAuthenticationFilter 자리)
    @Override
    public void configureClientInboundChannel(ChannelRegistration registration) {
        registration.interceptors(stompAuthInterceptor);
    }
}
