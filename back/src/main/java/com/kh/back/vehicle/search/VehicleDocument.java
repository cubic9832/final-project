package com.kh.back.vehicle.search;

import com.kh.back.vehicle.dto.VehicleDto;
import java.util.Map;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Mapping;
import org.springframework.data.elasticsearch.annotations.Setting;

/** ES 검색용 차량 문서. 검색어와 맞춰 볼 글자 필드만 두고, 가격·이미지 같은 값은 MySQL 에서 가져온다. */
@Getter
@Setter
@NoArgsConstructor
@Document(indexName = "vehicles", createIndex = false)
@Setting(settingPath = "elasticsearch/vehicle-settings.json")
@Mapping(mappingPath = "elasticsearch/vehicle-mappings.json")
public class VehicleDocument {
    // front vehicleApi.js 의 classLabels 와 같은 표기
    private static final Map<String, String> CLASS_LABELS = Map.of(
            "MINI", "경차",
            "SUBCOMPACT_SUV", "소형 SUV",
            "COMPACT_SEDAN", "준중형 세단",
            "COMPACT_SUV", "준중형 SUV",
            "MIDSIZE_SEDAN", "중형 세단",
            "MIDSIZE_SUV", "중형 SUV",
            "LARGE_SUV", "대형 SUV",
            "FULLSIZE_SEDAN", "대형 세단",
            "MPV", "승합");
    private static final Map<String, String> FUEL_LABELS = Map.of(
            "GASOLINE", "가솔린 휘발유",
            "HYBRID", "하이브리드",
            "DIESEL", "디젤 경유",
            "ELECTRIC", "전기차",
            "LPG", "LPG",
            "HYDROGEN", "수소차");
    private static final Map<String, String> CONDITION_LABELS = Map.of("NEW", "신차", "USED", "중고차");

    @Id
    private Long id;
    private String brand;
    private String name;
    private String trimName;
    private String powertrain;
    private String classLabel;
    private String fuelLabel;
    private String conditionLabel;

    public static VehicleDocument from(VehicleDto vehicle) {
        VehicleDocument document = new VehicleDocument();
        document.setId(vehicle.getId());
        document.setBrand(vehicle.getBrand());
        document.setName(vehicle.getName());
        document.setTrimName(vehicle.getTrimName());
        document.setPowertrain(vehicle.getPowertrain());
        document.setClassLabel(label(CLASS_LABELS, vehicle.getClassCode()));
        document.setFuelLabel(label(FUEL_LABELS, vehicle.getFuelCode()));
        document.setConditionLabel(label(CONDITION_LABELS, vehicle.getConditionCode()));
        return document;
    }

    private static String label(Map<String, String> labels, String code) {
        return code == null ? null : labels.getOrDefault(code, code);
    }
}
