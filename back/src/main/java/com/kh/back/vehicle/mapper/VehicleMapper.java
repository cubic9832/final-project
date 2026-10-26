package com.kh.back.vehicle.mapper;

import com.kh.back.vehicle.dto.VehicleDto;

import java.util.List;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface VehicleMapper {
    List<VehicleDto> findAll();
}
