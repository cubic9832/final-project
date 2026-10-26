package com.kh.back;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class BackApplicationTests {

    @Autowired
    private MockMvc mvc;

	@Test
	void contextLoads() {
	}

    @Test
    void relocatedVehicleMapperLoadsAndPublicCatalogUsesCommonResponse() throws Exception {
        mvc.perform(get("/api/v1/vehicles"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data").isArray());
    }

    @Test
    void unauthenticatedTasteAccessKeepsAuthenticationErrorContract() throws Exception {
        mvc.perform(get("/api/v1/members/me/current-taste"))
                .andExpect(status().isUnauthorized())
                .andExpect(content().contentTypeCompatibleWith("application/json"))
                .andExpect(jsonPath("$.error.code").value("AUTH_REQUIRED"));
    }

}
