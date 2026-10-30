package com.kh.back.chat.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

/**
 * 8단계: 상담 만족도 1건 (chat_feedback) + 평가받은 상담원 닉네임. 총관리자만 본다.
 */
@Getter
@Setter
@NoArgsConstructor
@ToString
public class ChatFeedbackDto {

    private Long id;
    private Long roomId;
    private Long adminId;
    private String adminNickName;
    private String memberNickName; // 평가한 회원 (전체 평가 목록에서만 채운다)
    private Integer rating;        // 1~5
    private String comment;        // 의견 (선택지 또는 기타에 쓴 글, 없으면 null)
    private boolean reported;      // 상담원 응대 신고
    private String reportReason;
    private LocalDateTime createdAt;
}
