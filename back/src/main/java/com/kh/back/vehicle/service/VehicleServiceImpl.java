package com.kh.back.vehicle.service;

import com.kh.back.vehicle.dto.VehicleResponse;
import com.kh.back.vehicle.mapper.VehicleMapper;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class VehicleServiceImpl implements VehicleService {
    private final VehicleMapper vehicleMapper;

    @Override
    @Transactional(readOnly = true)
    public List<VehicleResponse> getVehicles() {
        return vehicleMapper.findAll().stream().map(VehicleResponse::from).toList();
    }
}
