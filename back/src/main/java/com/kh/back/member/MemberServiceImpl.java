package com.kh.back.member;

import com.kh.back.auth.NickNamePolicy;
import com.kh.back.auth.PasswordChangeLimiter;
import com.kh.back.auth.RefreshTokenMapper;
import com.kh.back.common.exception.ApiException;
import java.time.LocalDate;
import java.time.Period;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class MemberServiceImpl implements MemberService {

    // 가입 · 입력 가능 나이 — 회원가입 AuthServiceImpl.MIN_SIGNUP_AGE · 화면 profileRules.js 와 같은 값 (운전면허 취득 가능 나이)
    private static final int MIN_AGE = 18;

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

    // 개인정보 수정 (6단계) — 개인정보 · 계정 관리 화면 [개인정보 저장]
    // 구글로 가입한 회원은 user_profiles 행이 없을 수 있어 upsert(없으면 만들고 있으면 바꾸기)로 저장한다
    @Override
    @Transactional
    public MemberResponse updateProfile(Long userId, ProfileUpdateRequest request) {
        MemberDto member = findMember(userId);
        UserProfileDto profile = userProfileMapper.findByUserId(userId);
        if (profile == null) {
            profile = new UserProfileDto();
            profile.setUserId(userId);
        }

        // 생년월일 · 성별: 보내지 않으면 그대로
        if (request.getBirthDate() != null) {
            // 회원가입과 같은 만 18세 검사 (구글 가입은 "만 18세 이상" 동의만 받았으므로 여기서 처음 확인된다)
            if (Period.between(request.getBirthDate(), LocalDate.now()).getYears() < MIN_AGE) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "AGE_RESTRICTED",
                        "만 " + MIN_AGE + "세 이상만 입력할 수 있습니다. 생년월일을 다시 확인해 주세요.");
            }
            profile.setBirthDate(request.getBirthDate());
        }
        if (request.getGender() != null) {
            profile.setGender(request.getGender());
        }

        // 선택 항목: null = 그대로, "" = 지우기, 값 = 바꾸기
        if (request.getPhone() != null) {
            profile.setPhone(request.getPhone().isBlank() ? null : request.getPhone().replace("-", "")); // 숫자만 저장
        }
        if (request.getDrivingExperience() != null) {
            profile.setDrivingExperience(blankToNull(request.getDrivingExperience()));
        }
        if (request.getPurchaseTiming() != null) {
            profile.setPurchaseTiming(blankToNull(request.getPurchaseTiming()));
        }

        userProfileMapper.upsert(profile);
        return MemberResponse.from(member, profile);
    }

    private static String blankToNull(String value) {
        return value.isBlank() ? null : value;
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
        } else if (lockedOrMismatch(userId, password, member)) {
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

    // 10-22: 5번 틀려 잠겼으면 비밀번호를 보지 않고 거절(429), 아니면 비밀번호가 틀렸는지
    private boolean lockedOrMismatch(Long userId, String password, MemberDto member) {
        passwordChangeLimiter.checkLocked(userId);
        return !passwordEncoder.matches(password, member.getPasswordHash());
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
