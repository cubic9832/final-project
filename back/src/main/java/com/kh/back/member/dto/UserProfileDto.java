package com.kh.back.member.dto;

import java.time.LocalDate;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * user_profiles 테이블 1행 (보완 5). 회원 1명당 1행이며, 보완 5 이전에 가입한 회원 · 구글로 가입한 회원은 행이 없을 수 있다.
 * 6단계: 운전 경력 · 구매 예정 시기 (V12, 둘 다 선택 항목)
 */
@Getter
@Setter
@NoArgsConstructor
public class UserProfileDto {

    private Long userId;
    private String phone;             // 숫자만 (예: 01012345678)
    private LocalDate birthDate;
    private String gender;            // MALE · FEMALE · NONE
    private String drivingExperience; // NONE · UNDER_1Y · YEARS_1_3 · OVER_3Y (6단계)
    private String purchaseTiming;    // WITHIN_3M · WITHIN_6M · WITHIN_1Y · UNDECIDED (6단계)
}
