package com.kh.back.member.service;

import com.kh.back.common.exception.ApiException;
import com.kh.back.member.dto.MemberDto;
import com.kh.back.member.dto.MemberResponse;
import com.kh.back.member.mapper.MemberMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class MemberServiceImpl implements MemberService {

    private final MemberMapper memberMapper;

    @Override
    @Transactional(readOnly = true)
    public MemberResponse getMember(Long userId) {
        MemberDto member = memberMapper.findById(userId);
        if (member == null) {
            // 토큰은 유효한데 회원이 탈퇴 등으로 사라진 경우
            throw new ApiException(HttpStatus.NOT_FOUND, "MEMBER_NOT_FOUND", "회원 정보를 찾을 수 없습니다.");
        }
        return MemberResponse.from(member);
    }
}
