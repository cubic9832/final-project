package com.kh.back.vehicle;

import java.math.BigDecimal;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class Vehicle {
    private Long id;
    private String brand;
    private String name;
    private String trimName;
    private Integer modelYear;
    private String conditionCode;
    private String classCode;
    private String fuelCode;
    private Integer seatingCapacity;
    private BigDecimal price;
    private BigDecimal efficiencyValue;
    private String efficiencyUnit;
    private String imageUrl;
    private String sourceName;
    private String sourceUrl;
    private Boolean isExample;
}
