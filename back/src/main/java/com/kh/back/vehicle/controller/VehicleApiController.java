package com.kh.back.vehicle.controller;

import com.kh.back.vehicle.dto.VehicleResponse;
import com.kh.back.vehicle.service.VehicleService;

import com.kh.back.common.dto.ApiResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/vehicles")
@RequiredArgsConstructor
public class VehicleApiController {
    private final VehicleService vehicleService;

    @GetMapping
    public ApiResponse<List<VehicleResponse>> list() {
        return ApiResponse.ok(vehicleService.getVehicles());
    }
}
