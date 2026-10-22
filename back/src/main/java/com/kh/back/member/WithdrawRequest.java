package com.kh.back.member;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 회원 탈퇴 요청 본문 (보완 4). 되돌릴 수 없는 작업이라 비밀번호를 한 번 더 확인한다.
 */
@Getter
@Setter
@NoArgsConstructor
public class WithdrawRequest {

    // 비밀번호로 가입한 회원: 비밀번호 확인 (없으면 MemberServiceImpl 이 400)
    private String password;

    // 보완 8: 구글로만 가입한 회원은 비밀번호가 없어 "탈퇴" 를 직접 입력해 확인한다
    private String confirmText;
}
