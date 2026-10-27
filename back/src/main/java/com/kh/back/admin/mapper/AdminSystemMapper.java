package com.kh.back.admin.mapper;

import org.apache.ibatis.annotations.Mapper;

// 7단계: 서비스 연결 상태 확인용 SQL (읽기만)
@Mapper
public interface AdminSystemMapper {

    // DB 가 응답하는지 (항상 1)
    int ping();

    // 마지막으로 성공한 Flyway 마이그레이션 번호
    String findLatestMigration();
}
