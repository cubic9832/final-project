package com.kh.back.member;

import com.kh.back.common.dto.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 로그인한 회원 본인의 정보.
 * SecurityConfig 규칙상 /api/v1/members/** 는 로그인이 필요하다 → 토큰이 없으면 이 Controller 에 오기 전에 401.
 */
@RestController
@RequestMapping("/api/v1/members")
@RequiredArgsConstructor
public class MemberApiController {

    private final MemberService memberService;

    // GET /api/v1/members/me — 내 정보
    // 호출: MyPage.jsx 화면이 열릴 때(useEffect) · [다시 시도] 버튼 → memberApi.getMe
    // 회원 번호는 요청 값으로 받지 않고, JwtAuthenticationFilter 가 토큰에서 꺼내 넣어 둔 값을 쓴다.
    // (요청 값으로 받으면 다른 사람 번호를 넣어 남의 정보를 볼 수 있기 때문)
    @GetMapping("/me")
    public ApiResponse<MemberResponse> me(@AuthenticationPrincipal Long userId) {
        return ApiResponse.ok(memberService.getMember(userId));
    }

    // PATCH /api/v1/members/me — 닉네임 변경 (보완 3 추가). 본문 { nickName }
    // 호출: MyPage.jsx [프로필 수정] → 팝업 [변경사항 저장] → memberApi.updateNickName
    // 토큰의 회원 번호만 쓴다 → 남의 닉네임은 바꿀 수 없다. 겹치면 409 NICKNAME_DUPLICATED
    @PatchMapping("/me")
    public ApiResponse<MemberResponse> updateNickName(@AuthenticationPrincipal Long userId,
                                                      @Valid @RequestBody NickNameUpdateRequest request) {
        return ApiResponse.ok(memberService.updateNickName(userId, request.getNickName()));
    }

    // DELETE /api/v1/members/me — 회원 탈퇴 (보완 4). 본문 { password }
    // 호출: MyPage.jsx 계정 및 데이터 [관리] → 탈퇴 팝업 [회원 탈퇴] 버튼 → memberApi.withdraw
    // 내 정보와 마찬가지로 토큰의 회원 번호만 쓴다 → 남의 계정은 탈퇴시킬 수 없다
    @DeleteMapping("/me")
    public ApiResponse<Void> withdraw(@AuthenticationPrincipal Long userId,
                                      @Valid @RequestBody WithdrawRequest request) {
        memberService.withdraw(userId, request.getPassword());
        return ApiResponse.ok(null);
    }
}
