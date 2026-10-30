package com.kh.back.chat.service;

import com.kh.back.chat.dto.ChatAdminOption;
import com.kh.back.chat.dto.ChatMessageDto;
import com.kh.back.chat.dto.ChatRoomDto;
import java.util.List;

/**
 * 8단계: 1:1 상담 채팅 (회원 ↔ 관리자).
 * 상태: 대기(WAITING) → [맡기] 진행 중(ACTIVE) → [상담 종료] 종료(CLOSED) → 회원이 [새로 상담하기] → 대기
 */
public interface ChatRoomService {

    // ── 회원 ──
    ChatRoomDto getMyRoom(Long userId);

    ChatRoomDto startConsultation(Long userId);

    void closeByMember(Long userId);

    // ── 회원 · 관리자 공통 ──
    boolean canView(Long viewerId, Long roomId);

    List<ChatMessageDto> getMessages(Long viewerId, Long roomId, Long beforeId, int size);

    ChatMessageDto sendMessage(Long senderId, Long roomId, String content);

    // ── 관리자 (관리자 · 총관리자) ──
    List<ChatRoomDto> getRooms(String status);

    List<ChatAdminOption> getAdmins();

    void assign(Long adminId, Long roomId);

    void transfer(Long actorId, Long roomId, Long toAdminId, String reason);

    void closeByAdmin(Long actorId, Long roomId);

    void restrict(Long actorId, Long roomId, int days, String reason);

    void unrestrict(Long actorId, Long roomId);

    void warn(Long actorId, Long roomId, String reason);

    void releaseRoomsOf(Long adminId);
}
