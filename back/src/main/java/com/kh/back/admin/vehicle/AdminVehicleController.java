package com.kh.back.admin.vehicle;

import com.kh.back.common.dto.ApiResponse;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/admin/vehicles")
@RequiredArgsConstructor
public class AdminVehicleController {
    private final AdminVehicleService service;
    @GetMapping public ApiResponse<List<AdminVehicleResponse>> list(){return ApiResponse.ok(service.list());}
    @GetMapping("/{id}") public ApiResponse<AdminVehicleResponse> get(@PathVariable String id){return ApiResponse.ok(service.get(id));}
    @PostMapping public ResponseEntity<ApiResponse<AdminVehicleResponse>> create(@Valid @RequestBody AdminVehicleRequest input,@AuthenticationPrincipal Long actor){
        var saved=service.save(null,input,actor);return ResponseEntity.created(URI.create("/api/v1/admin/vehicles/"+saved.id())).body(ApiResponse.ok(saved));
    }
    @PutMapping("/{id}") public ApiResponse<AdminVehicleResponse> update(@PathVariable String id,@Valid @RequestBody AdminVehicleRequest input,@AuthenticationPrincipal Long actor){return ApiResponse.ok(service.save(id,input,actor));}
}
