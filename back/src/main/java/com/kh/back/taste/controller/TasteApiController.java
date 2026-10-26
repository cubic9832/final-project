package com.kh.back.taste.controller;

import com.kh.back.taste.dto.CurrentTasteResponse;
import com.kh.back.taste.dto.TasteCatalogResponse;
import com.kh.back.taste.dto.TasteSaveRequest;
import com.kh.back.common.dto.ApiResponse;
import com.kh.back.taste.service.TasteService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/members/me")
@RequiredArgsConstructor
public class TasteApiController {
    private final TasteService service;

    @GetMapping("/taste-test")
    public ApiResponse<TasteCatalogResponse> catalog() {
        return ApiResponse.ok(service.catalog());
    }

    @GetMapping("/current-taste")
    public ResponseEntity<ApiResponse<CurrentTasteResponse>> current(@AuthenticationPrincipal Long userId) {
        var current = service.current(userId);
        return current == null ? ResponseEntity.noContent().build() : ResponseEntity.ok(ApiResponse.ok(current));
    }

    @PutMapping("/current-taste")
    public ApiResponse<CurrentTasteResponse> save(@AuthenticationPrincipal Long userId, @Valid @RequestBody TasteSaveRequest request) {
        return ApiResponse.ok(service.save(userId, request));
    }
}
