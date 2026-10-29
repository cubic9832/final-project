package com.kh.back.admin.vehicle;

import tools.jackson.databind.JsonNode;
import java.time.LocalDateTime;

public record AdminVehicleResponse(String id, long version, String status, LocalDateTime updatedAt, JsonNode vehicle) {}
