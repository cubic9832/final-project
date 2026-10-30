package com.kh.back.common.websocket;

import com.kh.back.chat.dto.ChatRoomDto;
import com.kh.back.chat.mapper.ChatMapper;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.common.security.CurrentRoleLookup;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

/**
 * 8단계: REST 의 JwtAuthenticationFilter 가 하던 일을 STOMP 에서 한다 (강의 샘플 step4 와 같은 구조).
 *   CONNECT   : 토큰을 확인하고, 이 연결이 누구의 것인지 기록한다
 *   SUBSCRIBE : 볼 수 있는 상담방인지 · 관리자 목록 알림은 관리자인지 (남의 상담을 엿듣지 못하게)
 *   SEND      : 정해 둔 주소만 (누가 쓸 수 있는지는 ChatRoomServiceImpl.sendMessage 가 본다 — 담당 상담원만 답장)
 * 브라우저 WebSocket 은 HTTP 헤더에 토큰을 실을 수 없어서 /ws 는 SecurityConfig 에서 열어 두고, 여기 CONNECT 에서 검사한다.
 */
@Component
@RequiredArgsConstructor
public class StompAuthInterceptor implements ChannelInterceptor {

    private static final Pattern ROOM_TOPIC = Pattern.compile("^/topic/chat/rooms/(\\d+)$"); // SUBSCRIBE
    private static final Pattern ROOM_APP = Pattern.compile("^/app/chat/rooms/(\\d+)$");     // SEND
    private static final String ADMIN_TOPIC = "/topic/admin/chat";
    private static final String MY_ERRORS = "/user/queue/errors";
    private static final Set<String> ADMIN_ROLES = Set.of("ADMIN", "SUPER_ADMIN");

    private final JwtProvider jwtProvider;
    // ChatRoomService 가 아니라 Mapper 를 쓴다 (샘플과 같음) — ChatRoomService → 메시지 보내는 도구 → WebSocket 설정 → 이 인터셉터로 서로 물려 서버가 시작하지 못한다
    private final ChatMapper chatMapper;
    private final CurrentRoleLookup currentRoleLookup;

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        StompHeaderAccessor accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
        StompCommand command = accessor.getCommand();

        // ① CONNECT — 토큰 확인. 연결 전체에서 한 번만 한다
        if (StompCommand.CONNECT.equals(command)) {
            String header = accessor.getFirstNativeHeader("Authorization"); // STOMP 헤더에서 꺼낸다
            if (header == null || !header.startsWith("Bearer ")) {
                throw new ApiException(HttpStatus.UNAUTHORIZED, "AUTH_REQUIRED", "로그인이 필요합니다.");
            }
            // 만료 · 위조면 JwtProvider 가 TOKEN_EXPIRED · TOKEN_INVALID 를 던진다 → 화면이 재발급 후 다시 연결
            Long userId = jwtProvider.parse(header.substring("Bearer ".length())).userId();

            // 이 연결의 주인을 기록한다. 이후 이 연결로 오는 모든 메시지에 자동으로 붙는다 (Principal)
            accessor.setUser(new UsernamePasswordAuthenticationToken(userId, null, List.of()));
        }

        // ② SUBSCRIBE · ③ SEND — 정해 둔 주소만
        if (StompCommand.SUBSCRIBE.equals(command) || StompCommand.SEND.equals(command)) {
            String destination = accessor.getDestination() == null ? "" : accessor.getDestination();
            Long userId = (Long) ((Authentication) accessor.getUser()).getPrincipal();

            if (StompCommand.SUBSCRIBE.equals(command)) {
                if (MY_ERRORS.equals(destination)) {
                    return message; // 내 오류 메시지 구독은 누구나
                }
                if (ADMIN_TOPIC.equals(destination)) {
                    // 상담 목록 알림은 관리자 · 총관리자만 (지금 DB 의 권한)
                    if (!ADMIN_ROLES.contains(currentRoleLookup.currentRole(userId))) {
                        throw forbidden("허용되지 않은 주소입니다.");
                    }
                    return message;
                }
                Matcher room = ROOM_TOPIC.matcher(destination);
                if (!room.matches()) {
                    throw forbidden("허용되지 않은 주소입니다.");
                }
                if (!canView(userId, Long.valueOf(room.group(1)))) {
                    throw forbidden("볼 수 없는 상담입니다.");
                }
            } else if (!ROOM_APP.matcher(destination).matches()) {
                throw forbidden("허용되지 않은 주소입니다.");
            }
        }

        return message;
    }

    // 볼 수 있는 상담방: 방 주인(회원) 또는 관리자 · 총관리자 (ChatRoomServiceImpl.canView 와 같은 규칙)
    private boolean canView(Long userId, Long roomId) {
        ChatRoomDto room = chatMapper.findRoomById(roomId);
        return room != null && (room.getUserId().equals(userId) || ADMIN_ROLES.contains(currentRoleLookup.currentRole(userId)));
    }

    private static ApiException forbidden(String message) {
        return new ApiException(HttpStatus.FORBIDDEN, "CHAT_FORBIDDEN", message);
    }
}
