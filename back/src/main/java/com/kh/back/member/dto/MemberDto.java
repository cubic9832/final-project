package com.kh.back.member.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

/**
 * users 테이블 1행. 암호화된 비밀번호까지 담고 있으므로 이 객체를 그대로 응답하지 않는다.
 * 응답에는 MemberResponse 를 쓴다.
 * (컬럼 password_hash, nick_name 은 map-underscore-to-camel-case 설정으로 passwordHash, nickName 에 자동 매핑)
 */
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = "passwordHash") // 로그에 비밀번호가 찍히지 않게
public class MemberDto {

    // 보완 8: 구글로만 가입한 회원의 password_hash 표시값. BCrypt 모양이 아니라서 어떤 비밀번호로도 로그인되지 않는다
    public static final String SOCIAL_ONLY_PASSWORD = "SOCIAL_ONLY";

    private Long id;
    private String email;
    private String passwordHash;
    private String nickName;
    private String role;           // USER · ADMIN
    private LocalDateTime createdAt;

    // 보완 8: 비밀번호 없이 구글로만 가입했는지 (회원 탈퇴 확인 방법이 달라진다)
    public boolean isSocialOnly() {
        return SOCIAL_ONLY_PASSWORD.equals(passwordHash);
    }
}
