package com.kh.back.admin.vehicle;

import java.util.List;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.converter.HttpMessageNotReadableException;

@Order(Ordered.HIGHEST_PRECEDENCE)
@RestControllerAdvice(assignableTypes={AdminVehicleController.class,AdminVehicleImageController.class})
public class AdminVehicleExceptionHandler {
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ProblemDetail> status(ResponseStatusException error){
        return ResponseEntity.status(error.getStatusCode()).body(ProblemDetail.forStatusAndDetail(error.getStatusCode(),error.getReason()==null?"요청을 처리할 수 없습니다.":error.getReason()));
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> fields(MethodArgumentNotValidException error){
        var problem=ProblemDetail.forStatusAndDetail(org.springframework.http.HttpStatus.BAD_REQUEST,"입력 항목을 확인해 주세요.");
        problem.setProperty("errors",error.getBindingResult().getFieldErrors().stream().map(e->java.util.Map.of("field",e.getField(),"message",e.getDefaultMessage()==null?"값을 확인해 주세요.":e.getDefaultMessage())).toList());
        return ResponseEntity.badRequest().body(problem);
    }
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ProblemDetail> unreadable(HttpMessageNotReadableException error){return ResponseEntity.badRequest().body(ProblemDetail.forStatusAndDetail(org.springframework.http.HttpStatus.BAD_REQUEST,"요청 형식을 확인해 주세요."));}
}
