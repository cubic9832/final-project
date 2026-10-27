package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminSystemStatus;
import com.kh.back.admin.mapper.AdminSystemMapper;
import java.lang.management.ManagementFactory;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class AdminSystemServiceImpl implements AdminSystemService {

    private final AdminSystemMapper adminSystemMapper;

    @Override
    public AdminSystemStatus getStatus() {
        // 이 요청에 응답하고 있다는 것 자체가 Spring API 가 켜져 있다는 뜻 → 켜진 시각만 알려 준다
        LocalDateTime startedAt = LocalDateTime.ofInstant(
                Instant.ofEpochMilli(ManagementFactory.getRuntimeMXBean().getStartTime()), ZoneId.systemDefault());
        long start = System.nanoTime();
        try {
            adminSystemMapper.ping();
            long millis = (System.nanoTime() - start) / 1_000_000;
            return new AdminSystemStatus(startedAt, true, millis, adminSystemMapper.findLatestMigration());
        } catch (DataAccessException e) {
            // DB 가 꺼졌거나 연결이 끊김 → 화면에 "연결 안 됨" (오류 내용은 로그에만)
            log.warn("admin system status: database check failed: {}", e.getMessage());
            return new AdminSystemStatus(startedAt, false, null, null);
        }
    }
}
