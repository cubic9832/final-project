package com.kh.back.vehicle;

import com.kh.back.common.dto.ApiResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/api/v1/vehicles")
@RequiredArgsConstructor
public class VehicleController {
    private final VehicleRepository vehicleRepository;

    @GetMapping
    public ApiResponse<List<VehicleResponse>> list() {
        return ApiResponse.ok(vehicleRepository.findAll().stream().map(VehicleResponse::from).toList());
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleFailure(Exception exception) {
        log.error("차량 목록 조회 실패", exception);
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR,
                "차량 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
    }
}
