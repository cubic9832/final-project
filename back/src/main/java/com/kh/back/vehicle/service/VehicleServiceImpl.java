package com.kh.back.vehicle.service;

import com.kh.back.vehicle.dto.VehicleDto;
import com.kh.back.vehicle.dto.VehicleResponse;
import com.kh.back.vehicle.mapper.VehicleMapper;
import com.kh.back.vehicle.search.VehicleSearchRepository;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class VehicleServiceImpl implements VehicleService {
    private final VehicleMapper vehicleMapper;
    private final VehicleSearchRepository vehicleSearchRepository;

    @Override
    @Transactional(readOnly = true)
    public List<VehicleResponse> getVehicles() {
        return vehicleMapper.findAll().stream().map(VehicleResponse::from).toList();
    }

    // ES 가 관련도 순 id 를 찾고, 응답 데이터는 원본인 MySQL 에서 그 순서대로 고른다
    @Override
    @Transactional(readOnly = true)
    public List<VehicleResponse> searchVehicles(String keyword) {
        List<Long> ids = vehicleSearchRepository.searchIds(keyword);
        if (ids.isEmpty()) return List.of();
        Map<Long, VehicleDto> vehicles = vehicleMapper.findAll().stream()
                .collect(Collectors.toMap(VehicleDto::getId, Function.identity()));
        return ids.stream().map(vehicles::get).filter(Objects::nonNull).map(VehicleResponse::from).toList();
    }
}
