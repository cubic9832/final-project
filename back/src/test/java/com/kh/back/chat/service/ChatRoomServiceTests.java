package com.kh.back.chat.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.kh.back.admin.mapper.AdminAuditLogMapper;
import com.kh.back.chat.dto.ChatMessageDto;
import com.kh.back.chat.dto.ChatRoomDto;
import com.kh.back.chat.mapper.ChatMapper;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.security.CurrentRoleLookup;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

// 8단계: 1:1 상담 규칙 — 회원은 내 방만 · 종료되면 못 씀, 관리자는 맡은 상담만 답장, 넘기기 · 종료는 담당자 또는 총관리자
@ExtendWith(MockitoExtension.class)
class ChatRoomServiceTests {

    static final long MEMBER = 7L;
    static final long OTHER_MEMBER = 8L;
    static final long ADMIN = 2L;
    static final long OTHER_ADMIN = 3L;
    static final long SUPER = 1L;
    static final long ROOM = 10L;

    @Mock ChatMapper chatMapper;
    @Mock ChatBroadcaster broadcaster;
    @Mock CurrentRoleLookup currentRoleLookup;
    @Mock AdminAuditLogMapper adminAuditLogMapper;
    @InjectMocks ChatRoomServiceImpl service;

    @BeforeEach
    void setUp() {
        lenient().when(currentRoleLookup.currentRole(MEMBER)).thenReturn("USER");
        lenient().when(currentRoleLookup.currentRole(OTHER_MEMBER)).thenReturn("USER");
        lenient().when(currentRoleLookup.currentRole(ADMIN)).thenReturn("ADMIN");
        lenient().when(currentRoleLookup.currentRole(OTHER_ADMIN)).thenReturn("ADMIN");
        lenient().when(currentRoleLookup.currentRole(SUPER)).thenReturn("SUPER_ADMIN");
        // 저장한 메시지를 다시 읽으면 같은 내용이 나온다고 가정
        lenient().when(chatMapper.findMessageById(any())).thenAnswer(inv -> new ChatMessageDto());
    }

    private ChatRoomDto room(String status, Long assignedAdminId) {
        ChatRoomDto room = new ChatRoomDto();
        room.setId(ROOM);
        room.setUserId(MEMBER);
        room.setStatus(status);
        room.setAssignedAdminId(assignedAdminId);
        room.setAssignedAdminNickName(assignedAdminId == null ? null : "상담원닉네임");
        lenient().when(chatMapper.findRoomById(ROOM)).thenReturn(room);
        lenient().when(chatMapper.findRoomByUserId(MEMBER)).thenReturn(room);
        return room;
    }

    private static void assertCode(Runnable call, String code) {
        assertThatThrownBy(call::run).isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo(code));
    }

    // ── 회원 ──

    @Test
    void 회원_화면에는_담당_관리자_닉네임을_보내지_않는다() {
        room(ChatRoomDto.ACTIVE, ADMIN);
        ChatRoomDto mine = service.getMyRoom(MEMBER);
        assertThat(mine.getAssignedAdminNickName()).isNull();
        assertThat(mine.getAssignedAdminId()).isNull();
    }

    @Test
    void 종료된_상담에서_새로_상담하면_대기로_되돌린다() {
        room(ChatRoomDto.CLOSED, ADMIN);
        when(chatMapper.reopen(ROOM)).thenReturn(1);
        service.startConsultation(MEMBER);
        verify(chatMapper).reopen(ROOM);
        verify(broadcaster).roomChanged(ROOM, ChatRoomDto.WAITING);
    }

    @Test
    void 종료된_상담에는_회원이_메시지를_보낼_수_없다() {
        room(ChatRoomDto.CLOSED, ADMIN);
        assertCode(() -> service.sendMessage(MEMBER, ROOM, "안녕하세요"), "CHAT_CLOSED");
    }

    @Test
    void 회원은_대기_중에도_메시지를_남길_수_있다() {
        room(ChatRoomDto.WAITING, null);
        service.sendMessage(MEMBER, ROOM, "  견적 문의합니다  ");
        ArgumentCaptor<ChatMessageDto> saved = ArgumentCaptor.forClass(ChatMessageDto.class);
        verify(chatMapper).insertMessage(saved.capture());
        assertThat(saved.getValue().getSenderType()).isEqualTo(ChatMessageDto.USER);
        assertThat(saved.getValue().getContent()).isEqualTo("견적 문의합니다"); // 앞뒤 공백 제거
    }

    @Test
    void 남의_상담방에는_보내거나_볼_수_없다() {
        room(ChatRoomDto.ACTIVE, ADMIN);
        assertCode(() -> service.sendMessage(OTHER_MEMBER, ROOM, "끼어들기"), "CHAT_FORBIDDEN");
        assertCode(() -> service.getMessages(OTHER_MEMBER, ROOM, null, 30), "CHAT_FORBIDDEN");
    }

    @Test
    void 빈_메시지와_1000자_넘는_메시지는_거절한다() {
        assertCode(() -> service.sendMessage(MEMBER, ROOM, "   "), "CHAT_INVALID");
        assertCode(() -> service.sendMessage(MEMBER, ROOM, "가".repeat(1001)), "CHAT_INVALID");
    }

    // ── 관리자 ──

    @Test
    void 담당이_아닌_관리자는_보기만_하고_답장할_수_없다() {
        room(ChatRoomDto.ACTIVE, ADMIN);
        assertThat(service.canView(OTHER_ADMIN, ROOM)).isTrue();
        assertCode(() -> service.sendMessage(OTHER_ADMIN, ROOM, "제가 답할게요"), "CHAT_FORBIDDEN");
    }

    @Test
    void 담당_관리자의_답장은_ADMIN_으로_저장된다() {
        room(ChatRoomDto.ACTIVE, ADMIN);
        service.sendMessage(ADMIN, ROOM, "안녕하세요, 상담원입니다.");
        ArgumentCaptor<ChatMessageDto> saved = ArgumentCaptor.forClass(ChatMessageDto.class);
        verify(chatMapper).insertMessage(saved.capture());
        assertThat(saved.getValue().getSenderType()).isEqualTo(ChatMessageDto.ADMIN);
    }

    @Test
    void 이미_다른_관리자가_맡았으면_맡기에_실패한다() {
        room(ChatRoomDto.ACTIVE, OTHER_ADMIN);
        when(chatMapper.assign(ROOM, ADMIN)).thenReturn(0); // 조건부 UPDATE 가 0줄 = 먼저 누른 사람이 있음
        assertCode(() -> service.assign(ADMIN, ROOM), "CHAT_ALREADY_ASSIGNED");
    }

    @Test
    void 일반_관리자는_남의_상담을_넘기거나_종료할_수_없다() {
        room(ChatRoomDto.ACTIVE, OTHER_ADMIN);
        assertCode(() -> service.transfer(ADMIN, ROOM, ADMIN, null), "CHAT_FORBIDDEN");
        assertCode(() -> service.closeByAdmin(ADMIN, ROOM), "CHAT_FORBIDDEN");
        verify(chatMapper, never()).transfer(anyLong(), anyLong(), anyLong());
    }

    @Test
    void 담당_관리자는_내_상담을_다른_관리자에게_넘기고_운영_로그에_이유를_남긴다() {
        room(ChatRoomDto.ACTIVE, ADMIN);
        when(chatMapper.transfer(ROOM, ADMIN, OTHER_ADMIN)).thenReturn(1);
        service.transfer(ADMIN, ROOM, OTHER_ADMIN, "휴가");
        verify(adminAuditLogMapper).insert(eq(ADMIN), eq("CHAT_TRANSFER"), eq("MEMBER"), eq(MEMBER), anyString());
        ArgumentCaptor<ChatMessageDto> notice = ArgumentCaptor.forClass(ChatMessageDto.class);
        verify(chatMapper).insertMessage(notice.capture());
        assertThat(notice.getValue().getContent()).isEqualTo("상담원이 바뀌었습니다."); // 이유는 회원에게 보이지 않는다
    }

    @Test
    void 총관리자는_남의_상담도_넘길_수_있다() {
        room(ChatRoomDto.ACTIVE, ADMIN);
        when(chatMapper.transfer(ROOM, ADMIN, OTHER_ADMIN)).thenReturn(1);
        service.transfer(SUPER, ROOM, OTHER_ADMIN, null);
        verify(chatMapper).transfer(ROOM, ADMIN, OTHER_ADMIN);
    }

    @Test
    void 관리자가_아닌_사람에게는_넘길_수_없다() {
        room(ChatRoomDto.ACTIVE, ADMIN);
        assertCode(() -> service.transfer(ADMIN, ROOM, OTHER_MEMBER, null), "CHAT_TARGET_NOT_ADMIN");
    }

    @Test
    void 관리자에서_해제되면_맡던_상담은_대기로_돌아간다() {
        when(chatMapper.findActiveRoomIdsByAdmin(ADMIN)).thenReturn(List.of(ROOM, 11L));
        service.releaseRoomsOf(ADMIN);
        verify(chatMapper).releaseByAdmin(ADMIN);
        verify(broadcaster).roomChanged(ROOM, ChatRoomDto.WAITING);
        verify(broadcaster).roomChanged(11L, ChatRoomDto.WAITING);
    }
}
