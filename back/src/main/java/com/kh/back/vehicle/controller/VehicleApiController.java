package com.kh.back.vehicle.controller;

import com.kh.back.vehicle.dto.VehicleResponse;
import com.kh.back.vehicle.service.VehicleService;

import com.kh.back.common.dto.ApiResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/vehicles")
@RequiredArgsConstructor
public class VehicleApiController {
    private final VehicleService vehicleService;

    // q 가 있으면 Elasticsearch 로 차명·브랜드·차종을 검색해 관련도 순으로 준다
    @GetMapping
    public ApiResponse<List<VehicleResponse>> list(@RequestParam(required = false) String q) {
        if (q == null || q.isBlank()) return ApiResponse.ok(vehicleService.getVehicles());
        return ApiResponse.ok(vehicleService.searchVehicles(q.strip()));
    }
}
