package com.kh.back.vehicle.service;

import com.kh.back.vehicle.dto.VehicleResponse;
import java.util.List;

public interface VehicleService {
    List<VehicleResponse> getVehicles();
}
