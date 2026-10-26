package com.kh.back.taste;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record TasteSaveRequest(@NotNull Integer version,
                               @NotNull @Size(min = 8, max = 8) List<@NotNull @Valid Answer> answers,
                               String expectedSavedAt) {
    public record Answer(@NotBlank String questionId, @NotNull Long optionId) {}
}
