package com.kh.back.admin.dto;

import java.time.LocalDateTime;

/**
 * 7단계: 관리자 운영 현황의 서비스 연결 상태 (Spring API · MySQL). 추천 서버는 화면이 Vite proxy 로 직접 확인한다.
 *
 * @param apiStartedAt     Spring 서버가 켜진 시각
 * @param databaseUp       MySQL 에 SELECT 1 이 되는지
 * @param databaseMillis   그 확인에 걸린 시간 (ms, 연결이 안 되면 null)
 * @param databaseVersion  마지막으로 적용된 Flyway 번호 (예: "14", 연결이 안 되면 null)
 */
public record AdminSystemStatus(LocalDateTime apiStartedAt, boolean databaseUp, Long databaseMillis, String databaseVersion) {
}
