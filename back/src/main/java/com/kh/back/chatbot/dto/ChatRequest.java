package com.kh.back.chatbot.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.List;

public record ChatRequest(@NotBlank @Size(max = 2000) String message,
                          @Size(max = 12) List<@NotNull @Valid Turn> history) {
    public record Turn(@NotBlank @Pattern(regexp = "user|model") String role,
                       @NotBlank @Size(max = 6000) String text) {}
}
