package com.kh.back.admin.dto;

import lombok.Getter;
import lombok.Setter;

// 7단계: "묶음 이름 + 개수" 한 줄 (날짜별 가입 수 · 나이대별 · 성별 집계 SQL 결과)
@Getter
@Setter
public class GroupCountRow {

    private String label;
    private int count;
}
