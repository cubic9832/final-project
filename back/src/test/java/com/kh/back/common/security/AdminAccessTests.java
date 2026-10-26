package com.kh.back.common.security;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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
}
