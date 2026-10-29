package com.kh.back.chatbot.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatGuideRequest(@NotBlank @Size(max = 80) String guideId) {}
