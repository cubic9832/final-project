package com.kh.back.admin.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.kh.back.admin.dto.AdminSystemStatus;
import com.kh.back.admin.mapper.AdminSystemMapper;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataAccessResourceFailureException;

// 7단계: 서비스 연결 상태 — DB 가 응답하면 번호까지, 꺼져 있으면 예외 없이 "연결 안 됨"
class AdminSystemServiceTests {

    private final AdminSystemMapper adminSystemMapper = mock(AdminSystemMapper.class);
    private final AdminSystemService service = new AdminSystemServiceImpl(adminSystemMapper);

    @Test
    void DB_가_응답하면_응답시간과_Flyway_번호를_준다() {
        when(adminSystemMapper.ping()).thenReturn(1);
        when(adminSystemMapper.findLatestMigration()).thenReturn("14");

        AdminSystemStatus status = service.getStatus();

        assertThat(status.apiStartedAt()).isNotNull();
        assertThat(status.databaseUp()).isTrue();
        assertThat(status.databaseMillis()).isNotNull();
        assertThat(status.databaseVersion()).isEqualTo("14");
    }

    @Test
    void DB_연결이_안_되면_예외_없이_연결_안_됨() {
        when(adminSystemMapper.ping()).thenThrow(new DataAccessResourceFailureException("down"));

        AdminSystemStatus status = service.getStatus();

        assertThat(status.databaseUp()).isFalse();
        assertThat(status.databaseMillis()).isNull();
        assertThat(status.databaseVersion()).isNull();
    }
}
