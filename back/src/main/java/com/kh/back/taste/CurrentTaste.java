package com.kh.back.taste;

import java.time.LocalDateTime;
import java.util.List;

public record CurrentTaste(int version, List<TasteSaveRequest.Answer> answers, String primary,
                          LocalDateTime savedAt) {}
