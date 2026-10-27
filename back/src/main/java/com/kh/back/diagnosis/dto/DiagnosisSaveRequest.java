package com.kh.back.diagnosis.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.PositiveOrZero;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 재무 진단 결과 저장 요청 본문 (마이페이지 "최근 재무 진단" 용 요약). 금액은 모두 원 단위.
 * 진단 계산은 화면(재무 진단 결과 화면)과 추천 서버가 이미 끝낸 값이고, 서버는 로그인한 회원의 기록으로 남기기만 한다.
 */
@Getter
@Setter
@NoArgsConstructor
public class DiagnosisSaveRequest {

    // 추천 서버 응답의 모델 버전 (예: candidate-v2) → model_versions 에 없으면 새로 등록
    @NotBlank(message = "모델 버전이 필요합니다.")
    @Pattern(regexp = "^[A-Za-z0-9._-]{1,50}$", message = "모델 버전 형식이 올바르지 않습니다.")
    private String modelVersion;

    @NotNull(message = "월 실수령액이 필요합니다.")
    @PositiveOrZero
    private Long monthlyIncome;        // 월 실수령 소득 (기타 정기소득 포함)

    @NotNull(message = "월 지출이 필요합니다.")
    @PositiveOrZero
    private Long monthlyExpense;       // 생활지출 합계 (대출 상환 제외)

    @NotNull(message = "월 여유금이 필요합니다.")
    private Long monthlyAvailable;     // 소득 - 지출 - 대출 상환 (마이너스일 수 있음)

    @NotNull(message = "사용 가능 예금이 필요합니다.")
    @PositiveOrZero
    private Long purchaseFunds;        // 차량 구매 · 유지에 쓸 수 있는 예금

    @PositiveOrZero
    private Long priceUpper;           // 구매 가격 상한 (산정 정보가 없으면 null)
}
