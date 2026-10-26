package com.kh.back.admin.mapper;

import com.kh.back.admin.dto.AdminAuditLogResponse;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

// 7단계: 관리자 작업 기록 (admin_audit_logs, V13)
@Mapper
public interface AdminAuditLogMapper {

    void insert(@Param("actorId") Long actorId, @Param("action") String action, @Param("targetType") String targetType,
                @Param("targetId") Long targetId, @Param("detail") String detail);

    // 최근 순. action 이 null 이면 전체
    List<AdminAuditLogResponse> findRecent(@Param("action") String action, @Param("offset") int offset, @Param("size") int size);

    int count(@Param("action") String action);
}
