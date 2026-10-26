package com.kh.back.member.mapper;

import com.kh.back.member.dto.UserAgreementDto;
import java.time.LocalDateTime;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

// 보완 9: 가입 동의 기록 · 이메일 알림 설정 (user_agreements, V14)
@Mapper
public interface UserAgreementMapper {

    void insert(UserAgreementDto agreement);

    UserAgreementDto findByUserId(Long userId);

    // 이메일 알림 바꾸기 — V14 이전 회원은 행이 없어서 없으면 만들고 있으면 바꾼다 (동의 시각은 건드리지 않음)
    void upsertNotification(@Param("userId") Long userId, @Param("emailNotification") String emailNotification,
                            @Param("updatesAgreedAt") LocalDateTime updatesAgreedAt);
}
