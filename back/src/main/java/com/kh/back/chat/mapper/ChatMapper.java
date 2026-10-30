package com.kh.back.chat.mapper;

import com.kh.back.chat.dto.ChatAdminOption;
import com.kh.back.chat.dto.ChatFeedbackDto;
import com.kh.back.chat.dto.ChatFeedbackSummary;
import com.kh.back.chat.dto.ChatMessageDto;
import com.kh.back.chat.dto.ChatQuickReply;
import com.kh.back.chat.dto.ChatRoomDto;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 8단계: 1:1 상담 채팅 DB 창구 (SQL 은 resources/mappers/ChatMapper.xml).
 */
@Mapper
public interface ChatMapper {

    ChatRoomDto findRoomById(@Param("roomId") Long roomId);

    ChatRoomDto findRoomByUserId(@Param("userId") Long userId);

    void insertRoom(ChatRoomDto room);

    // 상태 바꾸기는 "지금 상태" 를 조건으로 건다 → 두 관리자가 동시에 눌러도 한 명만 성공 (바뀐 줄 수로 판단)
    int reopen(@Param("roomId") Long roomId);

    int assign(@Param("roomId") Long roomId, @Param("adminId") Long adminId);

    int transfer(@Param("roomId") Long roomId, @Param("fromAdminId") Long fromAdminId, @Param("toAdminId") Long toAdminId);

    int close(@Param("roomId") Long roomId);

    List<Long> findActiveRoomIdsByAdmin(@Param("adminId") Long adminId);

    int releaseByAdmin(@Param("adminId") Long adminId);

    // 상담 제한: 지금부터 days 일 뒤까지 (풀면 NULL)
    void restrict(@Param("roomId") Long roomId, @Param("days") int days);

    void unrestrict(@Param("roomId") Long roomId);

    void warn(@Param("roomId") Long roomId);

    // 만족도 · 신고
    int closeFeedback(@Param("roomId") Long roomId);

    void insertFeedback(ChatFeedbackDto feedback);

    List<ChatFeedbackDto> findFeedbackByRoom(@Param("roomId") Long roomId);

    List<ChatFeedbackSummary> findFeedbackSummary();

    // 자주 쓰는 문구 (상담원마다)
    List<ChatQuickReply> findQuickReplies(@Param("adminId") Long adminId);

    int countQuickReplies(@Param("adminId") Long adminId);

    void insertQuickReply(@Param("adminId") Long adminId, @Param("content") String content);

    int deleteQuickReply(@Param("id") Long id, @Param("adminId") Long adminId);

    List<ChatRoomDto> findRooms(@Param("status") String status);

    void insertMessage(ChatMessageDto message);

    void touchLastMessage(@Param("roomId") Long roomId);

    ChatMessageDto findMessageById(@Param("messageId") Long messageId);

    List<ChatMessageDto> findMessages(@Param("roomId") Long roomId, @Param("beforeId") Long beforeId, @Param("size") int size);

    List<ChatAdminOption> findAdmins();
}
