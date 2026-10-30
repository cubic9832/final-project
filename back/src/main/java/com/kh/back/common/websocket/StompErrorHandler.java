package com.kh.back.common.websocket;

import com.kh.back.common.exception.ApiException;
import java.nio.charset.StandardCharsets;
import org.springframework.messaging.Message;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.StompSubProtocolErrorHandler;

/**
 * 8단계: 인터셉터에서 던진 예외는 Spring 이 감싸서(MessageDeliveryException) 처리한다 (강의 샘플 step4 와 같음).
 * 그대로 두면 ERROR 프레임에 긴 내부 메시지가 들어가므로, 우리 오류 코드만 담아 보낸다.
 * 화면은 frame.headers.message 로 TOKEN_EXPIRED 인지 알 수 있다 (REST 의 JwtAuthenticationEntryPoint 와 같은 역할).
 */
@Component
public class StompErrorHandler extends StompSubProtocolErrorHandler {

    @Override
    public Message<byte[]> handleClientMessageProcessingError(Message<byte[]> clientMessage, Throwable ex) {
        // 감싸진 예외 안에서 우리가 던진 ApiException 을 찾는다
        Throwable cause = ex;
        while (cause != null && !(cause instanceof ApiException)) {
            cause = cause.getCause();
        }

        if (cause instanceof ApiException e) {
            StompHeaderAccessor accessor = StompHeaderAccessor.create(StompCommand.ERROR);
            accessor.setMessage(e.getCode());          // 화면은 frame.headers.message 로 읽는다
            accessor.setLeaveMutable(true);
            return MessageBuilder.createMessage(
                    e.getMessage().getBytes(StandardCharsets.UTF_8), accessor.getMessageHeaders());
        }
        return super.handleClientMessageProcessingError(clientMessage, ex); // 그 밖의 오류는 기본 처리
    }
}
