package com.kh.back.admin.vehicle;

import java.net.URI;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.node.ObjectNode;

@Service
@RequiredArgsConstructor
public class AdminVehicleService {
    private final AdminVehicleRepository repository;
    private final ObjectMapper mapper;

    public List<AdminVehicleResponse> list() { return repository.findAll(); }
    public AdminVehicleResponse get(String id) {
        var row=repository.find(id);
        if(row==null)throw new ResponseStatusException(HttpStatus.NOT_FOUND,"차량을 찾을 수 없습니다.");
        return row;
    }
    @Transactional
    public AdminVehicleResponse save(String id,AdminVehicleRequest input,long actor) {
        var before=id==null?null:get(id);
        if(before!=null && (input.version()==null || before.version()!=input.version()))
            throw new ResponseStatusException(HttpStatus.CONFLICT,"다른 관리자가 수정했습니다. 목록을 새로고침한 후 다시 편집해 주세요.");
        if(!input.sourceUrl().isEmpty() && !webUrl(input.sourceUrl()))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"출처는 http 또는 https URL이어야 합니다.");
        if(!input.imageUrl().isEmpty() && !input.imageUrl().matches("/(images/recommendations/[a-zA-Z0-9/_-]+\\.webp|api/v1/vehicles/images/[a-f0-9-]+\\.(png|jpg|webp))"))
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"허용되지 않은 차량 이미지 경로입니다.");
        if(input.status().equals("PUBLISHED") && (input.bodyType()==null || input.seats()==null || input.lengthMm()==null || input.efficiency()==null || input.sourceUrl().isBlank() || input.checkedOn()==null))
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"공개하려면 차체 형태·정원·전장·연비와 출처·확인일을 입력해 주세요.");
        String key=id==null?"managed-"+UUID.randomUUID():id;
        ObjectNode value=before==null?mapper.createObjectNode():(ObjectNode)before.vehicle().deepCopy();
        value.put("id",key);value.put("brand",input.brand().strip());value.put("model",input.model().strip());value.put("year",input.year());value.put("trim",input.trim().strip());
        value.put("fuel",input.fuel());value.put("price",input.priceWon());value.set("efficiency",mapper.valueToTree(input.efficiency()));
        value.set("seats",mapper.valueToTree(input.seats()));value.set("length_mm",mapper.valueToTree(input.lengthMm()));value.set("body_type",mapper.valueToTree(input.bodyType()));
        value.put("origin",input.origin());value.put("drive",input.drive());value.put("image_url",input.imageUrl());value.put("source_url",input.sourceUrl());value.put("source_name",input.sourceName());
        value.put("checked_on",input.checkedOn()==null?"":input.checkedOn().toString());value.put("memo",input.memo());
        // Edited specifications replace old per-configuration assumptions and corrections.
        value.put("quality","admin-maintained");value.put("seats_status","admin-maintained");value.putArray("seat_options");
        value.putArray("body_source_urls").add(input.sourceUrl());value.put("space_source_url",input.sourceUrl());value.put("seats_source_url",input.sourceUrl());
        value.putNull("assumed_seat_range");value.putNull("default_configuration");value.put("efficiency_reference_only",false);
        if(before!=null && !before.vehicle().path("fuel").asText().equals(input.fuel()))value.putNull("original_fuel");
        String json=value.toString();
        if(before==null)repository.insert(key,json,input.status(),actor);
        else if(repository.update(key,input.version(),json,input.status(),actor)!=1)
            throw new ResponseStatusException(HttpStatus.CONFLICT,"다른 관리자가 먼저 수정했습니다.");
        repository.audit(key,actor,before,json,input.status());
        return get(key);
    }
    private boolean webUrl(String value) {
        try { var url=URI.create(value);return ("https".equals(url.getScheme())||"http".equals(url.getScheme()))&&url.getHost()!=null; }
        catch(IllegalArgumentException e){return false;}
    }
}
