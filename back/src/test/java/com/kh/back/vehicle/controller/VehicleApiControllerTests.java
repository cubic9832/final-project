package com.kh.back.vehicle.controller;

import com.kh.back.vehicle.dto.VehicleDto;
import com.kh.back.vehicle.mapper.VehicleMapper;
import com.kh.back.vehicle.service.VehicleServiceImpl;
import com.kh.back.common.exception.GlobalExceptionHandler;

import java.math.BigDecimal;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class VehicleApiControllerTests {
    private VehicleMapper repository;
    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        repository = mock(VehicleMapper.class);
        mvc = MockMvcBuilders.standaloneSetup(new VehicleApiController(new VehicleServiceImpl(repository)))
                .setControllerAdvice(new GlobalExceptionHandler()).build();
    }

    @Test
    void returnsVehiclePriceInWonAndSource() throws Exception {
        VehicleDto vehicle = new VehicleDto();
        vehicle.setId(42L);
        vehicle.setPrice(new BigDecimal("25550000.00"));
        vehicle.setPowertrain("1.6 하이브리드");
        vehicle.setDisplacementCc(1580);
        vehicle.setPriceBeforeIncentive(new BigDecimal("27000000.00"));
        vehicle.setCityEfficiency(new BigDecimal("21.0"));
        vehicle.setHighwayEfficiency(new BigDecimal("19.0"));
        vehicle.setWheelSizeInch(16);
        vehicle.setSourceUrl("https://www.hyundai.com/price.pdf");
        when(repository.findAll()).thenReturn(List.of(vehicle));
        mvc.perform(get("/api/v1/vehicles"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data[0].id").value(42))
                .andExpect(jsonPath("$.data[0].price").value(25550000))
                .andExpect(jsonPath("$.data[0].powertrain").value("1.6 하이브리드"))
                .andExpect(jsonPath("$.data[0].displacementCc").value(1580))
                .andExpect(jsonPath("$.data[0].priceBeforeIncentive").value(27000000))
                .andExpect(jsonPath("$.data[0].cityEfficiency").value(21.0))
                .andExpect(jsonPath("$.data[0].highwayEfficiency").value(19.0))
                .andExpect(jsonPath("$.data[0].wheelSizeInch").value(16))
                .andExpect(jsonPath("$.data[0].sourceUrl").value(vehicle.getSourceUrl()));
    }

    @Test
    void emptyCatalogIsSuccessful() throws Exception {
        when(repository.findAll()).thenReturn(List.of());
        mvc.perform(get("/api/v1/vehicles"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.data").isEmpty());
    }

    @Test
    void databaseFailureReturnsCommonErrorWithoutInternalDetails() throws Exception {
        when(repository.findAll()).thenThrow(new IllegalStateException("private database credentials"));
        mvc.perform(get("/api/v1/vehicles"))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentTypeCompatibleWith("application/json"))
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.error.code").value("INTERNAL_ERROR"))
                .andExpect(jsonPath("$.error.message").value("서버 오류가 발생했습니다."));
    }
}
