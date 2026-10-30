package com.kh.back.chat.service;

import com.kh.back.chat.dto.ChatQuickReply;
import java.util.List;

/**
 * 8단계: 상담원의 자주 쓰는 문구 (상담원마다 따로).
 */
public interface ChatQuickReplyService {

    List<ChatQuickReply> getMine(Long adminId);

    List<ChatQuickReply> add(Long adminId, String content);

    List<ChatQuickReply> delete(Long adminId, Long id);
}
