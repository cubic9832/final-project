package com.kh.back.taste.controller;

import com.kh.back.common.exception.ApiException;
import com.kh.back.common.exception.GlobalExceptionHandler;
import com.kh.back.taste.dto.CurrentTasteResponse;
import com.kh.back.taste.dto.TasteCatalogResponse;
import com.kh.back.taste.dto.TasteSaveRequest;
import com.kh.back.taste.service.TasteService;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;
import org.springframework.web.bind.support.WebDataBinderFactory;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class TasteApiControllerTests {
    private TasteService service;
    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        service = mock(TasteService.class);
        mvc = MockMvcBuilders.standaloneSetup(new TasteApiController(service))
                .setControllerAdvice(new GlobalExceptionHandler())
                .setCustomArgumentResolvers(new HandlerMethodArgumentResolver() {
                    @Override
                    public boolean supportsParameter(MethodParameter parameter) {
                        return parameter.hasParameterAnnotation(AuthenticationPrincipal.class);
                    }

                    @Override
                    public Object resolveArgument(MethodParameter parameter, ModelAndViewContainer container,
                                                  NativeWebRequest request, WebDataBinderFactory binder) {
                        return 7L;
                    }
                }).build();
    }

    @Test
    void catalogAndCurrentTasteUseCommonSuccessEnvelope() throws Exception {
        when(service.catalog()).thenReturn(new TasteCatalogResponse(1, 2, 8, Map.of(), List.of(), List.of()));
        when(service.current(7L)).thenReturn(currentTaste());
        mvc.perform(get("/api/v1/members/me/taste-test"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.questionCount").value(8));
        mvc.perform(get("/api/v1/members/me/current-taste"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.primary").value("city"));
    }

    @Test
    void absentCurrentTasteReturnsNoBody() throws Exception {
        mvc.perform(get("/api/v1/members/me/current-taste"))
                .andExpect(status().isNoContent()).andExpect(content().string(""));
    }

    @Test
    void saveReturnsSavedTasteAndConflictsKeepBusinessCode() throws Exception {
        when(service.save(eq(7L), any())).thenReturn(currentTaste())
                .thenThrow(new ApiException(HttpStatus.CONFLICT, "TASTE_CHANGED", "다른 화면에서 취향이 변경됐습니다."));
        mvc.perform(put("/api/v1/members/me/current-taste").contentType("application/json").content(validBody()))
                .andExpect(status().isOk()).andExpect(jsonPath("$.data.primary").value("city"));
        mvc.perform(put("/api/v1/members/me/current-taste").contentType("application/json").content(validBody()))
                .andExpect(status().isConflict())
                .andExpect(content().contentTypeCompatibleWith("application/json"))
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.error.code").value("TASTE_CHANGED"));
    }

    @Test
    void invalidAnswersAndMalformedJsonAreBadRequests() throws Exception {
        for (String body : List.of("{\"version\":2,\"answers\":[]}", "{")) {
            mvc.perform(put("/api/v1/members/me/current-taste").contentType("application/json").content(body))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error.code").value("BAD_REQUEST"));
        }
    }

    @Test
    void frameworkMethodAndContentTypeErrorsKeepTheirHttpStatus() throws Exception {
        mvc.perform(post("/api/v1/members/me/current-taste"))
                .andExpect(status().isMethodNotAllowed())
                .andExpect(header().exists("Allow"))
                .andExpect(jsonPath("$.error.code").value("METHOD_NOT_ALLOWED"));
        mvc.perform(put("/api/v1/members/me/current-taste").contentType("text/plain").content(validBody()))
                .andExpect(status().isUnsupportedMediaType())
                .andExpect(jsonPath("$.error.code").value("UNSUPPORTED_MEDIA_TYPE"));
    }

    private CurrentTasteResponse currentTaste() {
        return new CurrentTasteResponse(2, List.of(), "city", LocalDateTime.of(2026, 10, 26, 12, 0));
    }

    private String validBody() {
        String answers = String.join(",", Collections.nCopies(8, "{\"questionId\":\"start\",\"optionId\":1}"));
        return "{\"version\":2,\"answers\":[" + answers + "]}";
    }
}
