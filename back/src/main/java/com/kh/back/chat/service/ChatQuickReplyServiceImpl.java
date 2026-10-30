package com.kh.back.chat.service;

import com.kh.back.chat.dto.ChatQuickReply;
import com.kh.back.chat.mapper.ChatMapper;
import com.kh.back.common.exception.ApiException;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 8단계: 자주 쓰는 문구. 등록 · 삭제 후에는 바뀐 목록을 돌려준다 (화면이 다시 부르지 않게).
 * 문구도 메시지처럼 금칙어 검사를 한다 — 막힐 문구를 등록해 두면 보낼 때마다 실패하니까.
 */
@Service
@RequiredArgsConstructor
public class ChatQuickReplyServiceImpl implements ChatQuickReplyService {

    static final int MAX_COUNT = 20; // 상담원 1명당

    private final ChatMapper chatMapper;
    private final ChatContentFilter contentFilter;

    @Override
    public List<ChatQuickReply> getMine(Long adminId) {
        return chatMapper.findQuickReplies(adminId);
    }

    @Override
    @Transactional
    public List<ChatQuickReply> add(Long adminId, String content) {
        String text = content.strip();
        if (contentFilter.isBlocked(text)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "CHAT_BLOCKED_WORD", "부적절한 표현이 있는 문구는 등록할 수 없습니다.");
        }
        if (chatMapper.countQuickReplies(adminId) >= MAX_COUNT) {
            throw new ApiException(HttpStatus.CONFLICT, "CHAT_QUICK_REPLY_LIMIT", "자주 쓰는 문구는 " + MAX_COUNT + "개까지 등록할 수 있습니다.");
        }
        chatMapper.insertQuickReply(adminId, text);
        return getMine(adminId);
    }

    @Override
    @Transactional
    public List<ChatQuickReply> delete(Long adminId, Long id) {
        if (chatMapper.deleteQuickReply(id, adminId) == 0) {
            throw new ApiException(HttpStatus.NOT_FOUND, "CHAT_QUICK_REPLY_NOT_FOUND", "문구를 찾을 수 없습니다.");
        }
        return getMine(adminId);
    }
}
