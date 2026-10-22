package com.kh.back.vehicle;

import java.math.BigDecimal;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class VehicleResponse {
    private Long id;
    private String brand;
    private String name;
    private String trimName;
    private String powertrain;
    private Integer modelYear;
    private String conditionCode;
    private String classCode;
    private String fuelCode;
    private Integer seatingCapacity;
    private Integer displacementCc;
    private BigDecimal price;
    private BigDecimal priceBeforeIncentive;
    private BigDecimal efficiencyValue;
    private BigDecimal cityEfficiency;
    private BigDecimal highwayEfficiency;
    private String efficiencyUnit;
    private Integer wheelSizeInch;
    private String imageUrl;
    private String sourceName;
    private String sourceUrl;
    private Boolean isExample;

    public static VehicleResponse from(Vehicle vehicle) {
        VehicleResponse response = new VehicleResponse();
        response.setId(vehicle.getId());
        response.setBrand(vehicle.getBrand());
        response.setName(vehicle.getName());
        response.setTrimName(vehicle.getTrimName());
        response.setPowertrain(vehicle.getPowertrain());
        response.setModelYear(vehicle.getModelYear());
        response.setConditionCode(vehicle.getConditionCode());
        response.setClassCode(vehicle.getClassCode());
        response.setFuelCode(vehicle.getFuelCode());
        response.setSeatingCapacity(vehicle.getSeatingCapacity());
        response.setDisplacementCc(vehicle.getDisplacementCc());
        response.setPrice(vehicle.getPrice());
        response.setPriceBeforeIncentive(vehicle.getPriceBeforeIncentive());
        response.setEfficiencyValue(vehicle.getEfficiencyValue());
        response.setCityEfficiency(vehicle.getCityEfficiency());
        response.setHighwayEfficiency(vehicle.getHighwayEfficiency());
        response.setEfficiencyUnit(vehicle.getEfficiencyUnit());
        response.setWheelSizeInch(vehicle.getWheelSizeInch());
        response.setImageUrl(vehicle.getImageUrl());
        response.setSourceName(vehicle.getSourceName());
        response.setSourceUrl(vehicle.getSourceUrl());
        response.setIsExample(vehicle.getIsExample());
        return response;
    }
}
