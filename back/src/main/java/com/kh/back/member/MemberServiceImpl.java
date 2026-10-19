package com.kh.back.member;

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

    @Override
    @Transactional(readOnly = true)
    public MemberResponse getMember(Long userId) {
        // 보완 5: 개인 정보(user_profiles)를 함께 돌려준다. 보완 5 이전 가입 회원은 null
        return MemberResponse.from(findMember(userId), userProfileMapper.findByUserId(userId));
    }

    // 닉네임 변경 (보완 3 추가) — 마이페이지 [프로필 수정] 팝업
    // 회원가입과 같은 중복 금지: 먼저 세어 보고, 그사이 다른 사람이 먼저 바꿨으면 UNIQUE(V7) 오류로 한 번 더 막는다
    @Override
    @Transactional
    public MemberResponse updateNickName(Long userId, String nickName) {
        MemberDto member = findMember(userId);
        if (!nickName.equals(member.getNickName())) {
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
    @Override
    @Transactional
    public void withdraw(Long userId, String password) {
        MemberDto member = findMember(userId);

        // 되돌릴 수 없는 작업이라 비밀번호를 한 번 더 확인한다 (로그인과 같은 BCrypt 비교)
        if (!passwordEncoder.matches(password, member.getPasswordHash())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "PASSWORD_MISMATCH", "비밀번호가 올바르지 않습니다.");
        }

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
