package com.kh.back.member;

import java.time.LocalDate;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * user_profiles 테이블 1행 (보완 5). 회원 1명당 1행이며, 보완 5 이전에 가입한 회원은 행이 없다.
 */
@Getter
@Setter
@NoArgsConstructor
public class UserProfileDto {

    private Long userId;
    private String phone;          // 숫자만 (예: 01012345678)
    private LocalDate birthDate;
    private String gender;         // MALE · FEMALE · NONE
}
