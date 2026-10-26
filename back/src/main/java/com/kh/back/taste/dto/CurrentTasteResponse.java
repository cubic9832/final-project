package com.kh.back.taste.dto;

import java.time.LocalDateTime;
import java.util.List;

public record CurrentTasteResponse(int version, List<TasteSaveRequest.Answer> answers, String primary,
                          LocalDateTime savedAt) {}
