package com.kh.back.auth;

import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

/**
 * 만료된 refresh token 정리 (10-20, 5단계 한계 보완).
 * 로그아웃 없이 14일이 지나면 행이 DB 에 남는다 (재발급 때 만료로 거절되므로 동작에는 영향 없음) → 서버가 켜질 때와 매일 새벽 4시에 지운다.
 * 만료 시각은 저장할 때와 같은 서버 시간(LocalDateTime.now())으로 비교한다.
 */
@Slf4j
@Configuration
@EnableScheduling
@RequiredArgsConstructor
public class RefreshTokenCleanup {

    private final RefreshTokenMapper refreshTokenMapper;

    @EventListener(ApplicationReadyEvent.class)
    @Scheduled(cron = "0 0 4 * * *")
    public void deleteExpired() {
        int deleted = refreshTokenMapper.deleteExpired(LocalDateTime.now());
        log.info("expired refresh tokens deleted: {}", deleted);
    }
}
