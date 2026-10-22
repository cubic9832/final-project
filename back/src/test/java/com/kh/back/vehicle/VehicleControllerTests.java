package com.kh.back.vehicle;

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

class VehicleControllerTests {
    private VehicleRepository repository;
    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        repository = mock(VehicleRepository.class);
        mvc = MockMvcBuilders.standaloneSetup(new VehicleController(repository)).build();
    }

    @Test
    void returnsVehiclePriceInWonAndSource() throws Exception {
        Vehicle vehicle = new Vehicle();
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
    void databaseFailureReturnsProblemWithoutInternalDetails() throws Exception {
        when(repository.findAll()).thenThrow(new IllegalStateException("private database credentials"));
        mvc.perform(get("/api/v1/vehicles"))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.status").value(500))
                .andExpect(jsonPath("$.detail").value("차량 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."));
    }
}
