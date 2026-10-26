package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminAuditLogResponse;
import com.kh.back.admin.mapper.AdminAuditLogMapper;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AdminAuditLogServiceImpl implements AdminAuditLogService {

    private final AdminAuditLogMapper adminAuditLogMapper;

    @Override
    @Transactional(readOnly = true)
    public List<AdminAuditLogResponse> getLogs(String action, int page, int size) {
        return adminAuditLogMapper.findRecent(blankToNull(action), (page - 1) * size, size);
    }

    @Override
    @Transactional(readOnly = true)
    public int countLogs(String action) {
        return adminAuditLogMapper.count(blankToNull(action));
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value.trim();
    }
}
