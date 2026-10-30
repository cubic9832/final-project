package com.kh.back.chat.service;

import com.kh.back.chat.dto.ChatFeedbackDto;
import com.kh.back.chat.dto.ChatFeedbackRequest;
import com.kh.back.chat.dto.ChatFeedbackSummary;
import com.kh.back.chat.dto.ChatRoomDto;
import com.kh.back.chat.mapper.ChatMapper;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.security.CurrentRoleLookup;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 8단계: 상담 만족도 + 상담원 신고.
 *   - 회원: 상담원이 맡았던 상담이 끝나면 한 번 남긴다 (chat_room.feedback_open). 새로 상담하면 다시 열린다
 *   - 총관리자: 상담원별 평균 · 신고 수, 회원별 평가 내용을 본다 (신고당한 상담원 본인이 보지 않도록 일반 관리자는 못 본다)
 */
@Service
@RequiredArgsConstructor
public class ChatFeedbackServiceImpl implements ChatFeedbackService {

    private final ChatMapper chatMapper;
    private final ChatBroadcaster broadcaster;
    private final CurrentRoleLookup currentRoleLookup;
    private final ChatContentFilter contentFilter;

    @Override
    @Transactional
    public void submit(Long userId, ChatFeedbackRequest request) {
        ChatRoomDto room = chatMapper.findRoomByUserId(userId);
        if (room == null || !ChatRoomDto.CLOSED.equals(room.getStatus()) || !room.isFeedbackOpen()) {
            throw feedbackClosed();
        }
        String comment = blankToNull(request.getComment());
        String reportReason = request.isReported() ? blankToNull(request.getReportReason()) : null;
        if (request.isReported() && reportReason == null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "CHAT_INVALID", "신고 사유를 골라 주세요.");
        }
        // 기타에 직접 쓴 글도 메시지처럼 금칙어 검사
        if ((comment != null && contentFilter.isBlocked(comment)) || (reportReason != null && contentFilter.isBlocked(reportReason))) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "CHAT_BLOCKED_WORD", "부적절한 표현이 있어 저장할 수 없습니다.");
        }
        // 먼저 닫는다 → 두 번 눌러도 한 번만 저장 (조건부 UPDATE)
        if (chatMapper.closeFeedback(room.getId()) == 0) {
            throw feedbackClosed();
        }
        ChatFeedbackDto feedback = new ChatFeedbackDto();
        feedback.setRoomId(room.getId());
        feedback.setAdminId(room.getAssignedAdminId()); // 종료해도 담당자는 남아 있다 (새로 상담할 때 비운다)
        feedback.setRating(request.getRating());
        feedback.setComment(comment);
        feedback.setReported(request.isReported());
        feedback.setReportReason(reportReason);
        chatMapper.insertFeedback(feedback);
        if (request.isReported()) {
            broadcaster.roomChanged(room.getId(), ChatRoomDto.CLOSED); // 관리자 목록에 "신고" 배지
        }
    }

    @Override
    public List<ChatFeedbackDto> getRoomFeedback(Long actorId, Long roomId) {
        requireSuper(actorId);
        return chatMapper.findFeedbackByRoom(roomId);
    }

    @Override
    public List<ChatFeedbackSummary> getSummary(Long actorId) {
        requireSuper(actorId);
        return chatMapper.findFeedbackSummary();
    }

    // 전체 평가 목록: sort = low(평점 낮은순) · high(높은순) · latest(최신순, 모르는 값도 최신순)
    @Override
    public List<ChatFeedbackDto> getFeedback(Long actorId, String sort, boolean reportedOnly) {
        requireSuper(actorId);
        return chatMapper.findFeedback(sort, reportedOnly);
    }

    private void requireSuper(Long actorId) {
        if (!"SUPER_ADMIN".equals(currentRoleLookup.currentRole(actorId))) {
            throw new ApiException(HttpStatus.FORBIDDEN, "CHAT_FORBIDDEN", "만족도 · 신고는 총관리자만 볼 수 있습니다.");
        }
    }

    private static String blankToNull(String text) {
        return text == null || text.isBlank() ? null : text.strip();
    }

    private static ApiException feedbackClosed() {
        return new ApiException(HttpStatus.CONFLICT, "CHAT_FEEDBACK_CLOSED", "만족도를 남길 수 있는 상담이 없습니다.");
    }
}
