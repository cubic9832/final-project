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
        repository.lockCatalog();
        var before=id==null?null:get(id);
        if(before!=null && before.status().equals("DELETED")) throw new ResponseStatusException(HttpStatus.CONFLICT,"삭제된 차량은 먼저 복구해 주세요.");
        ensureUnique(id,input.brand(),input.model(),input.year(),input.trim(),input.fuel(),input.drive());
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
        value.set("monthly_insurance",mapper.valueToTree(input.monthlyInsurance()));
        value.set("monthly_tax",mapper.valueToTree(input.monthlyTax()));
        value.set("monthly_maintenance",mapper.valueToTree(input.monthlyMaintenance()));
        value.put("origin",input.origin());value.put("drive",input.drive());value.put("image_url",input.imageUrl());value.put("image_removed",input.imageUrl().isEmpty());value.put("source_url",input.sourceUrl());value.put("source_name",input.sourceName());
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
    private void ensureUnique(String id,String brand,String model,String year,String trim,String fuel,String drive) {
        boolean duplicate=repository.findAll().stream().anyMatch(row -> !row.id().equals(id) && !row.status().equals("DELETED")
            && row.vehicle().path("brand").asText().strip().equalsIgnoreCase(brand.strip())
            && row.vehicle().path("model").asText().strip().equalsIgnoreCase(model.strip())
            && row.vehicle().path("year").asText().equals(year)
            && row.vehicle().path("trim").asText().strip().equalsIgnoreCase(trim.strip())
            && row.vehicle().path("fuel").asText().equals(fuel)
            && row.vehicle().path("drive").asText("미확인").equals(drive));
        if(duplicate)throw new ResponseStatusException(HttpStatus.CONFLICT,"같은 브랜드·모델·연식·트림·연료·구동 방식의 차량이 이미 있습니다.");
    }
    @Transactional
    public AdminVehicleResponse changeDeleted(String id,long version,boolean deleted,long actor) {
        repository.lockCatalog();
        var before=get(id);
        if(before.version()!=version)throw new ResponseStatusException(HttpStatus.CONFLICT,"차량이 변경되었습니다. 목록을 새로고침해 주세요.");
        if(before.status().equals("DELETED")==deleted)return before;
        var v=before.vehicle();
        if(!deleted)ensureUnique(id,v.path("brand").asText(),v.path("model").asText(),v.path("year").asText(),v.path("trim").asText(),v.path("fuel").asText(),v.path("drive").asText("미확인"));
        String status=deleted?"DELETED":"DRAFT";
        if(repository.update(id,version,v.toString(),status,actor)!=1)throw new ResponseStatusException(HttpStatus.CONFLICT,"다른 관리자가 먼저 수정했습니다.");
        repository.audit(id,actor,before,v.toString(),status);
        return get(id);
    }
    private boolean webUrl(String value) {
        try { var url=URI.create(value);return ("https".equals(url.getScheme())||"http".equals(url.getScheme()))&&url.getHost()!=null; }
        catch(IllegalArgumentException e){return false;}
    }
}
