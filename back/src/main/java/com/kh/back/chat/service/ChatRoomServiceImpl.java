package com.kh.back.chat.service;

import com.kh.back.admin.mapper.AdminAuditLogMapper;
import com.kh.back.chat.dto.ChatAdminOption;
import com.kh.back.chat.dto.ChatMessageDto;
import com.kh.back.chat.dto.ChatRoomDto;
import com.kh.back.chat.mapper.ChatMapper;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.security.CurrentRoleLookup;
import java.util.List;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 8단계: 1:1 상담 채팅 규칙.
 * 권한은 "지금" DB 의 권한으로 본다 (CurrentRoleLookup, 7단계) — 관리자에서 해제된 사람의 토큰이 남아 있어도 상담은 못 한다.
 *   - 회원: 내 상담방만 보고, 종료되지 않았으면 쓴다
 *   - 관리자 · 총관리자: 모든 상담방을 보고, 내가 맡은 진행 중 상담에만 쓴다 (담당이 아니면 보기만)
 *   - 넘기기 · 종료: 담당 관리자 또는 총관리자 (총관리자는 휴가 · 퇴사한 관리자의 상담을 옮길 수 있다)
 */
@Service
@RequiredArgsConstructor
public class ChatRoomServiceImpl implements ChatRoomService {

    private static final int MAX_LENGTH = 1000; // chat_message.content VARCHAR(1000)
    private static final Set<String> ADMIN_ROLES = Set.of("ADMIN", "SUPER_ADMIN");

    private final ChatMapper chatMapper;
    private final ChatBroadcaster broadcaster;
    private final CurrentRoleLookup currentRoleLookup;
    private final AdminAuditLogMapper adminAuditLogMapper;

    // ───────────── 회원 ─────────────

    // 내 상담방 (없으면 null). 담당 관리자 닉네임은 지운다 — 회원 화면에는 "상담원" 으로만 보인다
    @Override
    public ChatRoomDto getMyRoom(Long userId) {
        ChatRoomDto room = chatMapper.findRoomByUserId(userId);
        if (room != null) {
            room.setAssignedAdminId(null);
            room.setAssignedAdminNickName(null);
        }
        return room;
    }

    // [1:1 상담] · [새로 상담하기]: 처음이면 방을 만들고, 종료됐으면 대기로 되돌린다. 대기 · 진행 중이면 그대로
    @Override
    @Transactional
    public ChatRoomDto startConsultation(Long userId) {
        ChatRoomDto room = chatMapper.findRoomByUserId(userId);
        if (room == null) {
            room = new ChatRoomDto();
            room.setUserId(userId);
            chatMapper.insertRoom(room);
            system(room.getId(), "상담을 요청했습니다. 상담원이 연결되면 이곳에서 대화할 수 있어요.");
            broadcaster.roomChanged(room.getId(), ChatRoomDto.WAITING);
        } else if (ChatRoomDto.CLOSED.equals(room.getStatus()) && chatMapper.reopen(room.getId()) == 1) {
            system(room.getId(), "새 상담을 요청했습니다. 상담원이 연결되면 알려 드릴게요.");
            broadcaster.roomChanged(room.getId(), ChatRoomDto.WAITING);
        }
        return getMyRoom(userId);
    }

    // 회원이 [상담 종료]
    @Override
    @Transactional
    public void closeByMember(Long userId) {
        ChatRoomDto room = chatMapper.findRoomByUserId(userId);
        if (room == null) {
            throw roomNotFound();
        }
        closeRoom(room.getId(), "회원이 상담을 종료했습니다.");
    }

    // ───────────── 공통 ─────────────

    // 이 방을 볼 수 있나: 방 주인(회원) 또는 관리자 · 총관리자 — WebSocket 구독(StompAuthInterceptor)과 REST 가 같은 규칙
    @Override
    public boolean canView(Long viewerId, Long roomId) {
        ChatRoomDto room = chatMapper.findRoomById(roomId);
        return room != null && (room.getUserId().equals(viewerId) || isAdmin(viewerId));
    }

    @Override
    public List<ChatMessageDto> getMessages(Long viewerId, Long roomId, Long beforeId, int size) {
        if (!canView(viewerId, roomId)) {
            throw forbidden("볼 수 없는 상담입니다.");
        }
        return chatMapper.findMessages(roomId, beforeId, size);
    }

    // 메시지 보내기 (STOMP SEND /app/chat/rooms/{id} → ChatMessageController)
    // 누가 보냈는지에 따라 USER · ADMIN 을 서버가 정한다 (화면이 보낸 값은 믿지 않는다)
    @Override
    @Transactional
    public ChatMessageDto sendMessage(Long senderId, Long roomId, String content) {
        String text = content == null ? "" : content.strip(); // 앞뒤 공백 제거
        if (text.isEmpty() || text.length() > MAX_LENGTH) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "CHAT_INVALID", "메시지는 1~1000자로 입력해 주세요.");
        }
        ChatRoomDto room = chatMapper.findRoomById(roomId);
        if (room == null) {
            throw roomNotFound();
        }

        String senderType;
        if (room.getUserId().equals(senderId)) {
            if (ChatRoomDto.CLOSED.equals(room.getStatus())) {
                throw new ApiException(HttpStatus.CONFLICT, "CHAT_CLOSED", "종료된 상담입니다. [새로 상담하기]를 눌러 주세요.");
            }
            senderType = ChatMessageDto.USER; // 대기 중에도 남겨 둘 수 있다 → 상담원이 맡으면 읽는다
        } else if (isAdmin(senderId)) {
            if (!ChatRoomDto.ACTIVE.equals(room.getStatus()) || !senderId.equals(room.getAssignedAdminId())) {
                throw forbidden("담당 상담원만 답장할 수 있습니다. 먼저 [맡기]를 눌러 주세요.");
            }
            senderType = ChatMessageDto.ADMIN;
        } else {
            throw forbidden("볼 수 없는 상담입니다.");
        }

        ChatMessageDto saved = save(roomId, senderType, senderId, text);
        broadcaster.roomChanged(roomId, room.getStatus());
        return saved;
    }

    // ───────────── 관리자 ─────────────

    @Override
    public List<ChatRoomDto> getRooms(String status) {
        if (status != null && !Set.of(ChatRoomDto.WAITING, ChatRoomDto.ACTIVE, ChatRoomDto.CLOSED).contains(status)) {
            status = null; // 모르는 값이면 전체
        }
        return chatMapper.findRooms(status);
    }

    @Override
    public List<ChatAdminOption> getAdmins() {
        return chatMapper.findAdmins();
    }

    // [맡기]: 대기 중인 상담만. 두 관리자가 동시에 눌러도 DB 의 조건부 UPDATE 로 한 명만 성공한다
    @Override
    @Transactional
    public void assign(Long adminId, Long roomId) {
        ChatRoomDto room = requireRoom(roomId);
        if (chatMapper.assign(roomId, adminId) == 0) {
            throw new ApiException(HttpStatus.CONFLICT, "CHAT_ALREADY_ASSIGNED",
                    ChatRoomDto.ACTIVE.equals(room.getStatus()) ? "이미 다른 상담원이 맡은 상담입니다." : "대기 중인 상담만 맡을 수 있습니다.");
        }
        system(roomId, "상담원이 연결되었습니다.");
        broadcaster.roomChanged(roomId, ChatRoomDto.ACTIVE);
    }

    // [넘기기]: 담당 관리자는 내 상담만, 총관리자는 어느 상담이든. 받는 사람의 수락 없이 바로 넘어간다
    // 이유는 운영 로그에만 (회원에게는 "상담원이 바뀌었습니다")
    @Override
    @Transactional
    public void transfer(Long actorId, Long roomId, Long toAdminId, String reason) {
        ChatRoomDto room = requireRoom(roomId);
        if (!ChatRoomDto.ACTIVE.equals(room.getStatus())) {
            throw new ApiException(HttpStatus.CONFLICT, "CHAT_NOT_ACTIVE", "진행 중인 상담만 넘길 수 있습니다.");
        }
        requireOwnerOrSuper(actorId, room, "내가 맡은 상담만 넘길 수 있습니다.");
        if (toAdminId.equals(room.getAssignedAdminId())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "CHAT_SAME_ADMIN", "지금 담당자에게는 넘길 수 없습니다.");
        }
        if (!isAdmin(toAdminId)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "CHAT_TARGET_NOT_ADMIN", "관리자에게만 넘길 수 있습니다.");
        }
        if (chatMapper.transfer(roomId, room.getAssignedAdminId(), toAdminId) == 0) {
            throw new ApiException(HttpStatus.CONFLICT, "CHAT_CHANGED", "그 사이 상담 상태가 바뀌었습니다. 목록을 새로고침해 주세요.");
        }
        String memo = reason == null || reason.isBlank() ? "" : " (" + reason.strip() + ")";
        // 운영 로그: 대상 = 상담받는 회원, 내용 = 누구 → 누구 + 이유 (같은 트랜잭션)
        adminAuditLogMapper.insert(actorId, "CHAT_TRANSFER", "MEMBER", room.getUserId(),
                "상담 넘김 #" + room.getAssignedAdminId() + " → #" + toAdminId + memo);
        system(roomId, "상담원이 바뀌었습니다.");
        broadcaster.roomChanged(roomId, ChatRoomDto.ACTIVE);
    }

    // [상담 종료] (관리자): 담당 관리자 또는 총관리자. 대기 중인 상담은 담당자가 없으니 총관리자만
    @Override
    @Transactional
    public void closeByAdmin(Long actorId, Long roomId) {
        ChatRoomDto room = requireRoom(roomId);
        requireOwnerOrSuper(actorId, room, "담당 상담원 또는 총관리자만 종료할 수 있습니다.");
        closeRoom(roomId, "상담원이 상담을 종료했습니다.");
    }

    // 관리자에서 해제될 때 (AdminMemberServiceImpl.changeRole): 맡던 진행 중 상담을 대기로 → 다른 관리자가 다시 맡는다
    @Override
    @Transactional
    public void releaseRoomsOf(Long adminId) {
        List<Long> roomIds = chatMapper.findActiveRoomIdsByAdmin(adminId);
        if (roomIds.isEmpty()) {
            return;
        }
        chatMapper.releaseByAdmin(adminId);
        for (Long roomId : roomIds) {
            system(roomId, "상담원 연결이 끊겨 다시 대기 중입니다. 곧 다른 상담원이 연결됩니다.");
            broadcaster.roomChanged(roomId, ChatRoomDto.WAITING);
        }
    }

    // ───────────── 도우미 ─────────────

    private void closeRoom(Long roomId, String notice) {
        if (chatMapper.close(roomId) == 0) {
            throw new ApiException(HttpStatus.CONFLICT, "CHAT_CLOSED", "이미 종료된 상담입니다.");
        }
        system(roomId, notice);
        broadcaster.roomChanged(roomId, ChatRoomDto.CLOSED);
    }

    // 연결 · 넘김 · 종료 안내 → 방에 SYSTEM 메시지로 남기고 실시간으로 보낸다 (회원 화면은 이걸 보고 상태를 다시 읽는다)
    private void system(Long roomId, String content) {
        save(roomId, ChatMessageDto.SYSTEM, null, content);
    }

    // 저장 → 마지막 메시지 시각 → 저장된 모양(번호 · 시각)으로 다시 읽어 방 구독자에게 보낸다
    private ChatMessageDto save(Long roomId, String senderType, Long senderId, String content) {
        ChatMessageDto message = new ChatMessageDto();
        message.setRoomId(roomId);
        message.setSenderType(senderType);
        message.setSenderId(senderId);
        message.setContent(content);
        chatMapper.insertMessage(message); // useGeneratedKeys → id 가 채워진다
        chatMapper.touchLastMessage(roomId);
        ChatMessageDto saved = chatMapper.findMessageById(message.getId());
        broadcaster.message(saved);
        return saved;
    }

    private void requireOwnerOrSuper(Long actorId, ChatRoomDto room, String message) {
        boolean owner = actorId.equals(room.getAssignedAdminId());
        if (!owner && !"SUPER_ADMIN".equals(currentRoleLookup.currentRole(actorId))) {
            throw forbidden(message);
        }
    }

    private ChatRoomDto requireRoom(Long roomId) {
        ChatRoomDto room = chatMapper.findRoomById(roomId);
        if (room == null) {
            throw roomNotFound();
        }
        return room;
    }

    private boolean isAdmin(Long userId) {
        return ADMIN_ROLES.contains(currentRoleLookup.currentRole(userId));
    }

    private static ApiException roomNotFound() {
        return new ApiException(HttpStatus.NOT_FOUND, "CHAT_ROOM_NOT_FOUND", "상담을 찾을 수 없습니다.");
    }

    private static ApiException forbidden(String message) {
        return new ApiException(HttpStatus.FORBIDDEN, "CHAT_FORBIDDEN", message);
    }
}
