package com.kh.back.taste;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

@Repository
@RequiredArgsConstructor
public class TasteRepository {
    private final JdbcTemplate jdbc;
    private final ObjectMapper json;

    public TasteCatalog catalog() {
        return jdbc.query("SELECT * FROM taste_test_versions WHERE status_code='PUBLISHED' ORDER BY version_no DESC LIMIT 1",
                (rs, row) -> loadCatalog(rs.getLong("test_version_id"), rs.getInt("version_no"), rs.getInt("question_count")))
                .stream().findFirst().orElseThrow(() -> new IllegalStateException("No published taste test"));
    }

    private TasteCatalog loadCatalog(long id, int version, int count) {
        Map<String, TasteCatalog.Type> types = new LinkedHashMap<>();
        jdbc.query("SELECT * FROM taste_types WHERE test_version_id=? ORDER BY display_order,taste_type_id", rs -> {
            long typeId = rs.getLong("taste_type_id");
            List<TasteCatalog.Vehicle> vehicles = jdbc.query("""
                    SELECT v.id, CONCAT(b.name,' ',v.name) name, v.class_code, v.image_url
                    FROM taste_type_vehicles tv JOIN vehicles v ON v.id=tv.vehicle_id JOIN brands b ON b.id=v.brand_id
                    WHERE tv.taste_type_id=? ORDER BY tv.display_order,v.id
                    """, (v, n) -> new TasteCatalog.Vehicle(v.getLong("id"), v.getString("name"),
                    v.getString("class_code"), v.getString("image_url")), typeId);
            types.put(rs.getString("type_code"), new TasteCatalog.Type(typeId, rs.getString("type_name"),
                    rs.getString("description"), json.readValue(rs.getString("tags_json"), new TypeReference<List<String>>() {}), vehicles));
        }, id);
        List<TasteCatalog.Question> questions = jdbc.query("SELECT * FROM taste_questions WHERE test_version_id=? ORDER BY step_no,question_id",
                (q, n) -> {
                    List<TasteCatalog.Option> options = jdbc.query("SELECT * FROM taste_options WHERE question_id=? ORDER BY display_order,option_id",
                            (o, m) -> {
                                Map<String, Integer> weights = new LinkedHashMap<>();
                                jdbc.query("SELECT t.type_code,s.score FROM taste_option_scores s JOIN taste_types t ON t.taste_type_id=s.taste_type_id WHERE s.option_id=?",
                                        s -> { weights.put(s.getString("type_code"), s.getInt("score")); }, o.getLong("option_id"));
                                return new TasteCatalog.Option(o.getLong("option_id"), o.getString("option_text"), weights);
                            }, q.getLong("question_id"));
                    return new TasteCatalog.Question(q.getString("question_code"), q.getLong("question_id"), q.getInt("step_no"),
                            q.getString("question_text"), q.getBoolean("is_default"), options);
                }, id);
        List<TasteCatalog.Branch> rules = jdbc.query("""
                SELECT s.question_code source_code,n.question_code next_code,r.trigger_option_id,r.condition_json
                FROM taste_branch_rules r JOIN taste_questions s ON s.question_id=r.source_question_id
                JOIN taste_questions n ON n.question_id=r.next_question_id
                WHERE s.test_version_id=? ORDER BY r.priority_no,r.branch_rule_id
                """, (r, n) -> new TasteCatalog.Branch(r.getString("source_code"), r.getObject("trigger_option_id", Long.class),
                r.getString("next_code"), r.getString("condition_json") == null ? null
                : json.readTree(r.getString("condition_json")).path("leadingType").asText()), id);
        return new TasteCatalog(id, version, count, types, questions, rules);
    }

    public boolean lockMember(long userId) {
        return !jdbc.queryForList("SELECT id FROM users WHERE id=? FOR UPDATE", Long.class, userId).isEmpty();
    }

    public CurrentTaste find(long userId) {
        return jdbc.query("""
                SELECT v.version_no,c.answers_json,t.type_code,c.saved_at
                FROM user_current_tastes c JOIN taste_types t ON t.taste_type_id=c.taste_type_id
                JOIN taste_test_versions v ON v.test_version_id=t.test_version_id WHERE c.user_id=?
                """, (r, n) -> new CurrentTaste(r.getInt("version_no"),
                json.readValue(r.getString("answers_json"), new TypeReference<List<TasteSaveRequest.Answer>>() {}),
                r.getString("type_code"), r.getTimestamp("saved_at").toLocalDateTime()), userId).stream().findFirst().orElse(null);
    }

    public void save(long userId, long typeId, List<TasteSaveRequest.Answer> answers) {
        jdbc.update("""
                INSERT INTO user_current_tastes(user_id,taste_type_id,answers_json,saved_at) VALUES (?,?,?,CURRENT_TIMESTAMP(6))
                ON DUPLICATE KEY UPDATE taste_type_id=VALUES(taste_type_id),answers_json=VALUES(answers_json),saved_at=VALUES(saved_at)
                """, userId, typeId, json.writeValueAsString(answers));
    }
}
