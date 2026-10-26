package com.kh.back.member;

import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 6단계: 개인정보 수정 요청 (PUT /api/v1/members/me/profile).
 * 값 규칙:
 * - birthDate · gender: 보내지 않으면(null) 지금 값 그대로. 생년월일은 만 18세 이상만 (Service 에서 검사)
 * - phone · drivingExperience · purchaseTiming (선택 항목): null = 그대로, "" = 지우기, 값 = 바꾸기
 *   (전화번호는 화면에 가린 값만 내려가므로, 바꾸지 않으면 null 로 보낸다)
 * 닉네임은 기존 PATCH /api/v1/members/me 를 그대로 쓴다 (중복 확인과 같이 움직이므로)
 */
@Getter
@Setter
@NoArgsConstructor
public class ProfileUpdateRequest {

    private LocalDate birthDate;

    @Pattern(regexp = "^(MALE|FEMALE|NONE)$", message = "성별을 다시 선택해 주세요.")
    private String gender;

    // 회원가입과 같은 형식 (010-1234-5678 · 01012345678), "" 는 지우기
    @Pattern(regexp = "^$|^010-?\\d{4}-?\\d{4}$", message = "전화번호는 010-1234-5678 형식으로 입력해 주세요.")
    private String phone;

    @Pattern(regexp = "^$|^(NONE|UNDER_1Y|YEARS_1_3|OVER_3Y)$", message = "운전 경력을 다시 선택해 주세요.")
    private String drivingExperience;

    @Pattern(regexp = "^$|^(WITHIN_3M|WITHIN_6M|WITHIN_1Y|UNDECIDED)$", message = "구매 예정 시기를 다시 선택해 주세요.")
    private String purchaseTiming;
}
