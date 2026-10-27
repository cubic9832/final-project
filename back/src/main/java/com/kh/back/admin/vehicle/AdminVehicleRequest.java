package com.kh.back.admin.vehicle;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDate;

public record AdminVehicleRequest(
    @NotBlank @Size(max=40) String brand,
    @NotBlank @Size(max=100) String model,
    @NotNull @Pattern(regexp="^$|[0-9]{4}") String year,
    @NotBlank @Size(max=300) String trim,
    @NotNull @Pattern(regexp="GASOLINE|HYBRID|DIESEL|ELECTRIC|LPG") String fuel,
    @Pattern(regexp="SEDAN|SUV|HATCHBACK|WAGON|MPV|BOX|PICKUP") String bodyType,
    @NotNull @Pattern(regexp="국산|수입") String origin,
    @NotNull @Min(1) @Max(10000000000L) Long priceWon,
    @DecimalMin(value="0",inclusive=false) @DecimalMax("100") BigDecimal efficiency,
    @Min(1) @Max(15) Integer seats,
    @Min(2500) @Max(6000) Integer lengthMm,
    @NotNull @Pattern(regexp="2WD|4WD|AWD|미확인") String drive,
    @NotNull @Pattern(regexp="DRAFT|REVIEW|PUBLISHED|DISCONTINUED") String status,
    @NotNull @Size(max=500) String imageUrl,
    @NotNull @Size(max=200) String sourceName,
    @NotNull @Size(max=2000) String sourceUrl,
    LocalDate checkedOn,
    @NotNull @Size(max=1000) String memo,
    @Min(0) @Max(10000000) Long monthlyInsurance,
    @Min(0) @Max(10000000) Long monthlyTax,
    @Min(0) @Max(10000000) Long monthlyMaintenance,
    @Positive Long version
) {}
