package com.kh.back.vehicle;

import java.util.List;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface VehicleRepository {
    List<VehicleResponse> findAll();
}
