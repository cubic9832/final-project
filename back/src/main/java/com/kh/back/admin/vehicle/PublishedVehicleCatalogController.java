package com.kh.back.admin.vehicle;

import com.kh.back.common.dto.ApiResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import tools.jackson.databind.JsonNode;

@RestController
@RequiredArgsConstructor
public class PublishedVehicleCatalogController {
    private final AdminVehicleRepository repository;
    @GetMapping("/api/v1/vehicles/recommendation-catalog")
    public ApiResponse<List<JsonNode>> catalog(){return ApiResponse.ok(repository.published());}
}
