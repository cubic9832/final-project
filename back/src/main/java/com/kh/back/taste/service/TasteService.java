package com.kh.back.taste.service;

import com.kh.back.taste.dto.CurrentTasteResponse;
import com.kh.back.taste.dto.TasteCatalogResponse;
import com.kh.back.taste.dto.TasteSaveRequest;

public interface TasteService {
    TasteCatalogResponse catalog();

    CurrentTasteResponse current(long userId);

    CurrentTasteResponse save(long userId, TasteSaveRequest request);
}
