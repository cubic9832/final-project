package com.kh.back.common.security;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.kh.back.common.jwt.JwtProvider;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

// 7단계: /api/v1/admin/** 는 ADMIN 만. 아직 관리 API 가 없어 없는 주소로 확인한다
// ADMIN 은 보안 검사를 통과해 404(주소 없음), 일반 회원은 403, 비회원은 401
@SpringBootTest
@AutoConfigureMockMvc
class AdminAccessTests {

    private static final String ADMIN_URL = "/api/v1/admin/access-check";

    @Autowired MockMvc mvc;
    @Autowired JwtProvider jwtProvider;

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

    // 권한 바꾸기는 총관리자만: 일반 관리자 403, 총관리자는 보안을 통과해 서비스까지 간다 (없는 회원이라 404)
    @Test
    void 권한_바꾸기는_총관리자만() throws Exception {
        String body = "{\"role\":\"ADMIN\"}";
        mvc.perform(patch("/api/v1/admin/members/999999/role").contentType("application/json").content(body)
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "ADMIN")))
                .andExpect(status().isForbidden());
        mvc.perform(patch("/api/v1/admin/members/999999/role").contentType("application/json").content(body)
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "SUPER_ADMIN")))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("MEMBER_NOT_FOUND"));
    }

    @Test
    void 총관리자도_관리자_화면_API를_쓴다() throws Exception {
        mvc.perform(get("/api/v1/admin/members/summary")
                        .header("Authorization", "Bearer " + jwtProvider.createAccessToken(1L, "SUPER_ADMIN")))
                .andExpect(status().isOk());
    }
}
