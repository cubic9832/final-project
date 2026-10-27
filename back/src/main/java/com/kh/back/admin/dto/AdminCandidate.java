package com.kh.back.admin.dto;

/**
 * 7단계: 관리자 추천 관리 — 추천 서버가 쓰는 후보 차량 한 건 (학습 결과 폴더의 catalog.json 에서 화면에 필요한 칸만).
 *
 * @param price       차량 가격 (원)
 * @param fuel        연료 코드 (GASOLINE · HYBRID · DIESEL · LPG · ELECTRIC)
 * @param efficiency  복합 연비 (km/L, 전기차는 km/kWh)
 * @param seatsStatus 승차 정원 확인 상태 (예: user-provided = 제조사 확인 전)
 * @param sourceUrl   가격 출처 (제조사 가격표)
 * @param checkedOn   출처를 확인한 날
 * @param quality     데이터 수집 방식 (예: automatically-extracted-snapshot)
 */
public record AdminCandidate(String id, String brand, String model, String trim, String year, Long price, String fuel,
                             Double efficiency, Integer lengthMm, String seatsLabel, String seatsStatus, String seatsNote,
                             String sourceUrl, String checkedOn, String quality) {
}
