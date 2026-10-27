package com.kh.back.admin.vehicle;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import tools.jackson.databind.ObjectMapper;

@Repository
@RequiredArgsConstructor
public class AdminVehicleRepository {
    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;

    public List<AdminVehicleResponse> findAll() {
        return jdbc.query("SELECT * FROM managed_vehicles ORDER BY updated_at DESC, id", (rs,n) ->
            new AdminVehicleResponse(rs.getString("id"),rs.getLong("version"),rs.getString("status"),rs.getTimestamp("updated_at").toLocalDateTime(),mapper.readTree(rs.getString("payload"))));
    }
    public AdminVehicleResponse find(String id) {
        var rows=jdbc.query("SELECT * FROM managed_vehicles WHERE id=?",(rs,n) ->
            new AdminVehicleResponse(rs.getString("id"),rs.getLong("version"),rs.getString("status"),rs.getTimestamp("updated_at").toLocalDateTime(),mapper.readTree(rs.getString("payload"))),id);
        return rows.isEmpty()?null:rows.get(0);
    }
    public void insert(String id,String payload,String status,long actor) {
        jdbc.update("INSERT INTO managed_vehicles(id,payload,status,updated_by) VALUES(?,?,?,?)",id,payload,status,actor);
    }
    public int update(String id,long version,String payload,String status,long actor) {
        return jdbc.update("UPDATE managed_vehicles SET payload=?,status=?,updated_by=?,version=version+1,updated_at=CURRENT_TIMESTAMP(6) WHERE id=? AND version=?",payload,status,actor,id,version);
    }
    public void audit(String id,long actor,AdminVehicleResponse before,String payload,String status) {
        jdbc.update("INSERT INTO managed_vehicle_changes(vehicle_id,actor_id,previous_payload,next_payload,previous_status,next_status) VALUES(?,?,?,?,?,?)",
            id,actor,before==null?null:before.vehicle().toString(),payload,before==null?null:before.status(),status);
    }
    public List<tools.jackson.databind.JsonNode> published() {
        return jdbc.query("SELECT payload FROM managed_vehicles WHERE status='PUBLISHED' ORDER BY id",(rs,n)->{
            var value=(tools.jackson.databind.node.ObjectNode)mapper.readTree(rs.getString(1));value.remove("memo");return value;
        });
    }
}
