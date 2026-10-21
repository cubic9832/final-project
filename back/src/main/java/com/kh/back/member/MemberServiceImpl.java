package com.kh.back.member;

import com.kh.back.auth.NickNamePolicy;
import com.kh.back.auth.PasswordChangeLimiter;
import com.kh.back.auth.RefreshTokenMapper;
import com.kh.back.common.exception.ApiException;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class MemberServiceImpl implements MemberService {

    private final MemberMapper memberMapper;
    private final UserProfileMapper userProfileMapper;
    private final PasswordEncoder passwordEncoder;
    private final PasswordChangeLimiter passwordChangeLimiter; // 보완 4 추가: 비밀번호 변경과 같은 "현재 비밀번호 틀린 횟수"
    private final RefreshTokenMapper refreshTokenMapper;

    @Override
    @Transactional(readOnly = true)
    public MemberResponse getMember(Long userId) {
        // 보완 5: 개인 정보(user_profiles)를 함께 돌려준다. 보완 5 이전 가입 회원은 null
        return MemberResponse.from(findMember(userId), userProfileMapper.findByUserId(userId));
    }

    // 닉네임 변경 (보완 3 추가) — 마이페이지 [프로필 수정] 팝업
    // 회원가입과 같은 중복 금지: 먼저 세어 보고, 그사이 다른 사람이 먼저 바꿨으면 UNIQUE(V7) 오류로 한 번 더 막는다
    // 보완 3 추가: 회원가입과 같은 금지어 검사 (바꿀 때만. 지금 닉네임 그대로 저장하면 검사하지 않는다)
    @Override
    @Transactional
    public MemberResponse updateNickName(Long userId, String nickName) {
        MemberDto member = findMember(userId);
        if (!nickName.equals(member.getNickName())) {
            String forbidden = NickNamePolicy.check(nickName);
            if (forbidden != null) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "NICKNAME_FORBIDDEN", forbidden);
            }
            if (memberMapper.countByNickName(nickName) > 0) {
                throw nickNameDuplicated();
            }
            try {
                memberMapper.updateNickName(userId, nickName);
            } catch (DuplicateKeyException e) {
                throw nickNameDuplicated();
            }
            member.setNickName(nickName);
        }
        return MemberResponse.from(member, userProfileMapper.findByUserId(userId));
    }

    private ApiException nickNameDuplicated() {
        return new ApiException(HttpStatus.CONFLICT, "NICKNAME_DUPLICATED", "이미 사용 중인 닉네임입니다.");
    }

    // 회원 탈퇴 (보완 4)
    // 한 트랜잭션: 중간에 하나라도 실패하면 모두 취소되어 "반만 탈퇴된" 상태가 생기지 않는다
    // noRollbackFor: 오류는 삭제 전에만 난다. 5번 틀려 로그아웃시킬 때 지운 refresh token 이 롤백으로 되살아나지 않게 (보완 4 추가)
    @Override
    @Transactional(noRollbackFor = ApiException.class)
    public void withdraw(Long userId, String password, String confirmText) {
        MemberDto member = findMember(userId);

        if (member.isSocialOnly()) {
            // 보완 8: 구글로만 가입한 회원은 비밀번호가 없다 → "탈퇴" 를 직접 입력했는지로 확인
            if (!"탈퇴".equals(confirmText == null ? null : confirmText.trim())) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "CONFIRM_TEXT_MISMATCH", "확인을 위해 \"탈퇴\"를 정확히 입력해 주세요.");
            }
        } else if (password == null || password.isBlank()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "비밀번호를 입력해 주세요.");
        } else if (!passwordEncoder.matches(password, member.getPasswordHash())) {
            // 되돌릴 수 없는 작업이라 비밀번호를 한 번 더 확인한다 (로그인과 같은 BCrypt 비교)
            // 보완 4 추가: 비밀번호 변경과 합쳐 5번 틀리면 모든 기기 로그아웃 (맞히는 순간 계정이 지워지므로)
            ApiException failure = passwordChangeLimiter.mismatch(userId, "비밀번호가 올바르지 않습니다.");
            if (PasswordChangeLimiter.LOGOUT_CODE.equals(failure.getCode())) {
                refreshTokenMapper.deleteByUserId(userId);
            }
            throw failure;
        }
        passwordChangeLimiter.reset(userId);

        // users 를 참조하는 데이터를 먼저 정리한 뒤 회원을 삭제한다 (외래키 때문에 순서가 중요)
        memberMapper.deleteFavoriteVehicles(userId);
        memberMapper.deletePurchasePlans(userId);
        memberMapper.detachInputSnapshots(userId);
        memberMapper.deleteById(userId); // refresh_token(V6) · user_profiles(V8, 보완 5)는 ON DELETE CASCADE 로 함께 삭제 → 다른 브라우저 로그인도 끝남
    }

    private MemberDto findMember(Long userId) {
        MemberDto member = memberMapper.findById(userId);
        if (member == null) {
            // 토큰은 유효한데 회원이 탈퇴 등으로 사라진 경우
            throw new ApiException(HttpStatus.NOT_FOUND, "MEMBER_NOT_FOUND", "회원 정보를 찾을 수 없습니다.");
        }
        return member;
    }
}
