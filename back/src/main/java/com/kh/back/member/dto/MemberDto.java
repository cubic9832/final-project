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

    private Long id;
    private String email;
    private String passwordHash;
    private String nickName;
    private String role;           // USER · ADMIN
    private LocalDateTime createdAt;
}
