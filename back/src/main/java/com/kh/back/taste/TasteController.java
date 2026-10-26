package com.kh.back.taste;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/members/me")
@RequiredArgsConstructor
public class TasteController {
    private final TasteRepository repository;
    private final TasteService service;

    @GetMapping("/taste-test")
    public TasteCatalog catalog() { return repository.catalog(); }

    @GetMapping("/current-taste")
    public org.springframework.http.ResponseEntity<CurrentTaste> current(@AuthenticationPrincipal Long userId) {
        var current = repository.find(userId);
        return current == null ? org.springframework.http.ResponseEntity.noContent().build() : org.springframework.http.ResponseEntity.ok(current);
    }

    @PutMapping("/current-taste")
    public CurrentTaste save(@AuthenticationPrincipal Long userId, @Valid @RequestBody TasteSaveRequest request) {
        return service.save(userId,request);
    }
}
