package com.kh.back.vehicle.dto;

import java.math.BigDecimal;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class VehicleDto {
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
}
