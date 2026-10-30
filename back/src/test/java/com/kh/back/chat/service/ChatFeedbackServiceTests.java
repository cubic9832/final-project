package com.kh.back.chat.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.chat.dto.ChatFeedbackDto;
import com.kh.back.chat.dto.ChatFeedbackRequest;
import com.kh.back.chat.dto.ChatRoomDto;
import com.kh.back.chat.mapper.ChatMapper;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.security.CurrentRoleLookup;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

// 8단계: 상담 만족도 · 신고 — 상담원이 맡았던 끝난 상담에 한 번, 신고는 사유 필수, 보는 것은 총관리자만
@ExtendWith(MockitoExtension.class)
class ChatFeedbackServiceTests {

    static final long MEMBER = 7L;
    static final long ADMIN = 2L;
    static final long SUPER = 1L;
    static final long ROOM = 10L;

    @Mock ChatMapper chatMapper;
    @Mock ChatBroadcaster broadcaster;
    @Mock CurrentRoleLookup currentRoleLookup;
    @Spy ChatContentFilter contentFilter = new ChatContentFilter();
    @InjectMocks ChatFeedbackServiceImpl service;

    @BeforeEach
    void setUp() {
        lenient().when(currentRoleLookup.currentRole(ADMIN)).thenReturn("ADMIN");
        lenient().when(currentRoleLookup.currentRole(SUPER)).thenReturn("SUPER_ADMIN");
    }

    private ChatRoomDto room(String status, boolean feedbackOpen) {
        ChatRoomDto room = new ChatRoomDto();
        room.setId(ROOM);
        room.setUserId(MEMBER);
        room.setStatus(status);
        room.setAssignedAdminId(ADMIN);
        room.setFeedbackOpen(feedbackOpen);
        when(chatMapper.findRoomByUserId(MEMBER)).thenReturn(room);
        return room;
    }

    private static ChatFeedbackRequest request(int rating, String comment, boolean reported, String reason) {
        ChatFeedbackRequest request = new ChatFeedbackRequest();
        request.setRating(rating);
        request.setComment(comment);
        request.setReported(reported);
        request.setReportReason(reason);
        return request;
    }

    private static void assertCode(Runnable call, String code) {
        assertThatThrownBy(call::run).isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo(code));
    }

    @Test
    void 끝난_상담의_만족도는_담당_상담원_앞으로_저장된다() {
        room(ChatRoomDto.CLOSED, true);
        when(chatMapper.closeFeedback(ROOM)).thenReturn(1);
        service.submit(MEMBER, request(5, "궁금한 점이 해결됐어요", false, "무시되는 사유"));
        ArgumentCaptor<ChatFeedbackDto> saved = ArgumentCaptor.forClass(ChatFeedbackDto.class);
        verify(chatMapper).insertFeedback(saved.capture());
        assertThat(saved.getValue().getAdminId()).isEqualTo(ADMIN);
        assertThat(saved.getValue().getRating()).isEqualTo(5);
        assertThat(saved.getValue().getReportReason()).isNull(); // 신고하지 않으면 사유는 버린다
        verify(broadcaster, never()).roomChanged(anyLong(), anyString());
    }

    @Test
    void 진행_중이거나_이미_남긴_상담에는_만족도를_남길_수_없다() {
        room(ChatRoomDto.ACTIVE, false);
        assertCode(() -> service.submit(MEMBER, request(4, null, false, null)), "CHAT_FEEDBACK_CLOSED");
        room(ChatRoomDto.CLOSED, false);
        assertCode(() -> service.submit(MEMBER, request(4, null, false, null)), "CHAT_FEEDBACK_CLOSED");
        verify(chatMapper, never()).insertFeedback(any());
    }

    @Test
    void 신고는_사유가_있어야_하고_관리자_목록에_알린다() {
        room(ChatRoomDto.CLOSED, true);
        assertCode(() -> service.submit(MEMBER, request(1, null, true, "  ")), "CHAT_INVALID");
        when(chatMapper.closeFeedback(ROOM)).thenReturn(1);
        service.submit(MEMBER, request(1, null, true, "불친절한 응대"));
        verify(broadcaster).roomChanged(ROOM, ChatRoomDto.CLOSED);
    }

    @Test
    void 기타에_쓴_글도_금칙어를_검사한다() {
        room(ChatRoomDto.CLOSED, true);
        assertCode(() -> service.submit(MEMBER, request(1, "상담원 병신", false, null)), "CHAT_BLOCKED_WORD");
        verify(chatMapper, never()).closeFeedback(anyLong());
    }

    @Test
    void 만족도와_신고는_총관리자만_본다() {
        assertCode(() -> service.getSummary(ADMIN), "CHAT_FORBIDDEN");
        assertCode(() -> service.getRoomFeedback(ADMIN, ROOM), "CHAT_FORBIDDEN");
        service.getSummary(SUPER);
        verify(chatMapper).findFeedbackSummary();
    }
}
