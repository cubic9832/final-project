package com.kh.back.common.security;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import static org.mockito.Mockito.when;

import com.kh.back.common.jwt.JwtProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

// 7단계: /api/v1/admin/** 는 관리자 · 총관리자만. 없는 주소로 확인하면 관리자는 보안을 통과해 404, 일반 회원 403, 비회원 401
// 관리자 API 는 DB 의 지금 권한을 다시 보므로(CurrentRoleLookup), 테스트에서는 회원 번호별 권한을 정해 둔다
// 1번 = 관리자, 2번 = 일반 회원, 3번 = 총관리자, 4번 = 토큰은 관리자지만 DB 에서는 해제된 회원
@SpringBootTest
@AutoConfigureMockMvc
class AdminAccessTests {

    private static final String ADMIN_URL = "/api/v1/admin/access-check";

    @Autowired MockMvc mvc;
    @Autowired JwtProvider jwtProvider;
    @MockitoBean CurrentRoleLookup currentRoleLookup;

    @BeforeEach
    void setUp() {
        when(currentRoleLookup.currentRole(1L)).thenReturn("ADMIN");
        when(currentRoleLookup.currentRole(2L)).thenReturn("USER");
        when(currentRoleLookup.currentRole(3L)).thenReturn("SUPER_ADMIN");
        when(currentRoleLookup.currentRole(4L)).thenReturn("USER");
    }

    @Test
    void 관리자는_보안_검사를_통과한다() throws Exception {
        String token = jwtProvider.createAccessToken(1L, "ADMIN");
        mvc.perform(get(ADMIN_URL).header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());
    }

    @Test
    void 일반_회원은_403() throws Exception {
        String token = jwtProvider.createAccessToken(2L, "USER");
        mvc.perform(get(ADMIN_URL).header("Authorization", "Bearer " + token))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("ACCESS_DENIED"));
    }

    @Test
    void 비회원은_401() throws Exception {
        mvc.perform(get(ADMIN_URL))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void 관리자는_회원_현황을_볼_수_있다() throws Exception {
        String token = jwtProvider.createAccessToken(1L, "ADMIN");
        mvc.perform(get("/api/v1/admin/members/summary").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.daily.length()").value(7))
                .andExpect(jsonPath("$.data.ageBands[5].label").value("미입력"));
        mvc.perform(get("/api/v1/admin/members?size=5").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.meta.size").value(5));
    }

    // 운영 현황(할 일 · 재무 진단 이용 현황): 관리자 200 (7일 막대 7칸), 일반 회원 403
    @Test
    void 관리자는_운영_현황을_볼_수_있다() throws Exception {
        mvc.perform(get("/api/v1/admin/overview")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "ADMIN")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.diagnoses.daily.length()").value(7))
                .andExpect(jsonPath("$.data.profileMissing").isNumber());
        mvc.perform(get("/api/v1/admin/overview")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(2L, "USER")))
                .andExpect(status().isForbidden());
    }

    // 모델 관리: git 에 있는 학습 결과 파일(ml/outputs/...)을 읽는다, 일반 회원 403
    @Test
    void 관리자는_모델_학습_결과를_볼_수_있다() throws Exception {
        mvc.perform(get("/api/v1/admin/model-report")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "ADMIN")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.available").value(true))
                .andExpect(jsonPath("$.data.metrics.length()").value(3))
                .andExpect(jsonPath("$.data.testPairAccuracy").isNumber());
        mvc.perform(get("/api/v1/admin/model-report")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(2L, "USER")))
                .andExpect(status().isForbidden());
    }

    // 서비스 연결 상태: 관리자는 실제 DB 확인 결과, 일반 회원 403
    @Test
    void 관리자는_서비스_연결_상태를_볼_수_있다() throws Exception {
        mvc.perform(get("/api/v1/admin/system-status")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "ADMIN")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.databaseUp").value(true))
                .andExpect(jsonPath("$.data.databaseVersion").isNotEmpty());
        mvc.perform(get("/api/v1/admin/system-status")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(2L, "USER")))
                .andExpect(status().isForbidden());
    }

    // 권한 바꾸기는 총관리자만: 일반 관리자 403, 총관리자는 보안을 통과해 서비스까지 간다 (없는 회원이라 404)
    @Test
    void 권한_바꾸기는_총관리자만() throws Exception {
        String body = "{\"role\":\"ADMIN\"}";
        mvc.perform(patch("/api/v1/admin/members/999999/role").contentType("application/json").content(body)
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "ADMIN")))
                .andExpect(status().isForbidden());
        mvc.perform(patch("/api/v1/admin/members/999999/role").contentType("application/json").content(body)
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(3L, "SUPER_ADMIN")))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("TARGET_MEMBER_NOT_FOUND"));
    }

    @Test
    void 총관리자도_관리자_화면_API를_쓴다() throws Exception {
        mvc.perform(get("/api/v1/admin/members/summary")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(3L, "SUPER_ADMIN")))
                .andExpect(status().isOk());
    }

    @Test
    void 관리자는_운영_로그를_볼_수_있다() throws Exception {
        mvc.perform(get("/api/v1/admin/audit-logs?size=3")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "ADMIN")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.meta.size").value(3));
    }

    // 해제된 관리자: 토큰에는 아직 ADMIN 이 남아 있어도(최대 30분) DB 가 USER 면 바로 403
    @Test
    void 관리자를_해제하면_토큰이_남아_있어도_바로_403() throws Exception {
        mvc.perform(get("/api/v1/admin/members/summary")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(4L, "ADMIN")))
                .andExpect(status().isForbidden());
    }
}
