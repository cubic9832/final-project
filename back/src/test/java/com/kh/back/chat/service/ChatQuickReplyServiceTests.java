package com.kh.back.chat.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.chat.mapper.ChatMapper;
import com.kh.back.common.exception.ApiException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

// 8단계: 상담원의 자주 쓰는 문구 — 앞뒤 공백 제거 · 금칙어 거절 · 20개 제한 · 내 문구만 삭제
@ExtendWith(MockitoExtension.class)
class ChatQuickReplyServiceTests {

    static final long ADMIN = 2L;

    @Mock ChatMapper chatMapper;
    @Spy ChatContentFilter contentFilter = new ChatContentFilter();
    @InjectMocks ChatQuickReplyServiceImpl service;

    private static void assertCode(Runnable call, String code) {
        assertThatThrownBy(call::run).isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo(code));
    }

    @Test
    void 문구는_앞뒤_공백을_빼고_등록한다() {
        service.add(ADMIN, "  확인 후 바로 안내해 드리겠습니다.  ");
        verify(chatMapper).insertQuickReply(ADMIN, "확인 후 바로 안내해 드리겠습니다.");
    }

    @Test
    void 금칙어가_있는_문구는_등록할_수_없다() {
        assertCode(() -> service.add(ADMIN, "씨발"), "CHAT_BLOCKED_WORD");
        verify(chatMapper, never()).insertQuickReply(anyLong(), anyString());
    }

    @Test
    void 문구는_20개까지만() {
        when(chatMapper.countQuickReplies(ADMIN)).thenReturn(20);
        assertCode(() -> service.add(ADMIN, "안녕하세요"), "CHAT_QUICK_REPLY_LIMIT");
    }

    @Test
    void 남의_문구는_지울_수_없다() {
        when(chatMapper.deleteQuickReply(99L, ADMIN)).thenReturn(0); // admin_id 조건에 안 맞아 0줄
        assertCode(() -> service.delete(ADMIN, 99L), "CHAT_QUICK_REPLY_NOT_FOUND");
    }
}
