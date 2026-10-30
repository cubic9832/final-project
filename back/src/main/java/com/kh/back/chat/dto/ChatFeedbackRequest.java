package com.kh.back.chat.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 8단계: 상담 만족도 { "rating": 4, "comment": "궁금한 점이 해결됐어요", "reported": false, "reportReason": null }.
 * 의견 · 신고 사유는 화면에서 선택지를 고르거나 [기타] 에 직접 쓴 글. 신고하면 사유가 꼭 있어야 한다 (ChatFeedbackServiceImpl).
 */
@Getter
@Setter
@NoArgsConstructor
public class ChatFeedbackRequest {

    @NotNull(message = "별점을 골라 주세요.")
    @Min(value = 1, message = "별점은 1~5점입니다.")
    @Max(value = 5, message = "별점은 1~5점입니다.")
    private Integer rating;

    @Size(max = 200, message = "의견은 200자까지 쓸 수 있습니다.")
    private String comment;

    private boolean reported;

    @Size(max = 200, message = "신고 사유는 200자까지 쓸 수 있습니다.")
    private String reportReason;
}
