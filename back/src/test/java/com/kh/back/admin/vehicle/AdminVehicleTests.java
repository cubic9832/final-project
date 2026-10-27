package com.kh.back.admin.vehicle;

import com.kh.back.common.jwt.JwtProvider;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import tools.jackson.databind.ObjectMapper;
import java.util.Map;
import java.util.HashMap;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.mock.web.MockMultipartFile;
import java.nio.file.Files;
import java.nio.file.Path;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class AdminVehicleTests {
    static final Path images;
    static {try{images=Files.createTempDirectory("vehicle-admin-images-");}catch(java.io.IOException e){throw new ExceptionInInitializerError(e);}}
    @DynamicPropertySource static void imageDirectory(DynamicPropertyRegistry registry){registry.add("vehicle-management.image-directory",()->images.toString());}
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired JwtProvider jwt;
    @Autowired JdbcTemplate jdbc;
    private String admin(){
        jdbc.update("INSERT INTO users(id,email,password_hash,nick_name,role) VALUES(999999,?,?,?,?) ON DUPLICATE KEY UPDATE role=VALUES(role)","vehicle-api-test@example.com","test-only","차량 API 테스트","ADMIN");
        return "Bearer "+jwt.createAccessToken(999999L,"ADMIN");
    }
    private Map<String,Object> request(){
        var v=new HashMap<String,Object>();
        v.putAll(Map.of("brand","테스트","model","관리자 저장 테스트","year","2026","trim","기본","fuel","ELECTRIC","bodyType","SUV","origin","국산","priceWon",30000000,"efficiency",5.5,"seats",5));
        v.putAll(Map.of("lengthMm",4400,"drive","2WD","status","DRAFT","imageUrl","","sourceName","공식 자료","sourceUrl","https://example.com/official","checkedOn","2026-10-26","memo","내부 메모"));
        return v;
    }
    @Test void duplicateDeletionRestoreAndCosts() throws Exception {
        var payload=request(); payload.put("monthlyInsurance",0);payload.put("monthlyTax",25000);payload.put("monthlyMaintenance",45000);
        String created=mvc.perform(post("/api/v1/admin/vehicles").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
        String id=mapper.readTree(created).path("data").path("id").asText();
        mvc.perform(post("/api/v1/admin/vehicles").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isConflict());
        mvc.perform(get("/api/v1/admin/vehicles/"+id).header("Authorization",admin())).andExpect(jsonPath("$.data.vehicle.monthly_insurance").value(0)).andExpect(jsonPath("$.data.vehicle.monthly_maintenance").value(45000));
        mvc.perform(patch("/api/v1/admin/vehicles/"+id+"/deletion").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content("{\"version\":1,\"deleted\":true}")).andExpect(status().isOk()).andExpect(jsonPath("$.data.status").value("DELETED"));
        mvc.perform(patch("/api/v1/admin/vehicles/"+id+"/deletion").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content("{\"version\":1,\"deleted\":false}")).andExpect(status().isConflict());
        mvc.perform(patch("/api/v1/admin/vehicles/"+id+"/deletion").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content("{\"version\":2,\"deleted\":false}")).andExpect(status().isOk()).andExpect(jsonPath("$.data.status").value("DRAFT"));
        payload.put("monthlyTax",-1);
        mvc.perform(post("/api/v1/admin/vehicles").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isBadRequest());
    }
    @Test void onlyAdministratorsCanManageVehicles() throws Exception {
        mvc.perform(get("/api/v1/admin/vehicles")).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/admin/vehicles").header("Authorization","Bearer "+jwt.createAccessToken(1L,"USER"))).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/admin/vehicles").header("Authorization",admin())).andExpect(status().isOk());
    }
    @Test void superAdministratorCanManageVehicles() throws Exception {
        admin();
        jdbc.update("UPDATE users SET role='SUPER_ADMIN' WHERE id=999999");
        mvc.perform(get("/api/v1/admin/vehicles").header("Authorization","Bearer "+jwt.createAccessToken(999999L,"SUPER_ADMIN"))).andExpect(status().isOk());
    }
    @Test void savePublishWithdrawAndStaleEditHavePersistentEffects() throws Exception {
        var payload=request();
        String created=mvc.perform(post("/api/v1/admin/vehicles").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload)))
            .andExpect(status().isCreated()).andExpect(header().exists("Location")).andReturn().getResponse().getContentAsString();
        String id=mapper.readTree(created).path("data").path("id").asText();
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM managed_vehicle_changes WHERE vehicle_id=?",Integer.class,id)).isEqualTo(1);
        mvc.perform(get("/api/v1/admin/vehicles/"+id).header("Authorization",admin())).andExpect(jsonPath("$.data.vehicle.price").value(30000000));
        assertThat(jdbc.queryForObject("SELECT status FROM managed_vehicles WHERE id=?",String.class,id)).isEqualTo("DRAFT");
        payload.put("status","PUBLISHED");payload.put("version",1);payload.put("priceWon",32000000);
        mvc.perform(put("/api/v1/admin/vehicles/"+id).header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isOk()).andExpect(jsonPath("$.data.version").value(2));
        mvc.perform(put("/api/v1/admin/vehicles/"+id).header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isConflict());
        String catalog=mvc.perform(get("/api/v1/vehicles/recommendation-catalog")).andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
        var row=java.util.stream.StreamSupport.stream(mapper.readTree(catalog).path("data").spliterator(),false).filter(v->id.equals(v.path("id").asText())).findFirst().orElseThrow();
        assertThat(row.path("price").asLong()).isEqualTo(32000000);assertThat(row.has("memo")).isFalse();
        payload.put("status","DISCONTINUED");payload.put("version",2);
        mvc.perform(put("/api/v1/admin/vehicles/"+id).header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isOk());
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM managed_vehicles WHERE id=? AND status='PUBLISHED'",Integer.class,id)).isZero();
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM managed_vehicle_changes WHERE vehicle_id=?",Integer.class,id)).isEqualTo(3);
    }
    @Test void invalidAndIncompletePublishedInputsAreRejected() throws Exception {
        var payload=request();payload.put("priceWon",0);
        mvc.perform(post("/api/v1/admin/vehicles").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isBadRequest()).andExpect(jsonPath("$.errors").isArray());
        payload.put("priceWon",30000000);payload.put("status","PUBLISHED");payload.remove("bodyType");
        mvc.perform(post("/api/v1/admin/vehicles").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isBadRequest());
        payload.put("bodyType","SUV");payload.put("imageUrl","https://example.com/arbitrary-image");
        mvc.perform(post("/api/v1/admin/vehicles").header("Authorization",admin()).contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(payload))).andExpect(status().isBadRequest());
    }
    @Test void imageUploadsRequireAdminAndValidateContents() throws Exception {
        var fake=new MockMultipartFile("file","car.png","image/png","not an image".getBytes());
        mvc.perform(multipart("/api/v1/admin/vehicle-images").file(fake)).andExpect(status().isUnauthorized());
        mvc.perform(multipart("/api/v1/admin/vehicle-images").file(fake).header("Authorization",admin())).andExpect(status().isBadRequest());
        var picture=new java.awt.image.BufferedImage(2,2,java.awt.image.BufferedImage.TYPE_INT_RGB);
        var bytes=new java.io.ByteArrayOutputStream();javax.imageio.ImageIO.write(picture,"png",bytes);
        String response=mvc.perform(multipart("/api/v1/admin/vehicle-images").file(new MockMultipartFile("file","../../car.png","image/png",bytes.toByteArray())).header("Authorization",admin()))
            .andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
        String url=mapper.readTree(response).path("data").path("url").asText();
        Path saved=images.resolve(url.substring(url.lastIndexOf('/')+1));
        try{
            assertThat(saved).hasParent(images);assertThat(Files.readAllBytes(saved)).isEqualTo(bytes.toByteArray());
            mvc.perform(get(url)).andExpect(status().isOk()).andExpect(content().contentTypeCompatibleWith("image/png"));
        }finally{Files.deleteIfExists(saved);}
    }
}
