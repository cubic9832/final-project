package com.kh.back.taste;

import com.kh.back.common.exception.ApiException;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Order(Ordered.HIGHEST_PRECEDENCE)
@RestControllerAdvice(assignableTypes = TasteController.class)
public class TasteExceptionHandler {
    @ExceptionHandler(ApiException.class)
    public ProblemDetail business(ApiException error) {
        var problem = ProblemDetail.forStatusAndDetail(error.getStatus(),error.getMessage());
        problem.setProperty("code",error.getCode());
        return problem;
    }

    @ExceptionHandler({MethodArgumentNotValidException.class,HttpMessageNotReadableException.class})
    public ProblemDetail input(Exception error) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST,"질문 버전과 8개 답변을 확인해 주세요.");
    }
}
