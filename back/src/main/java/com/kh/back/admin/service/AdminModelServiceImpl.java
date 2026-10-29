package com.kh.back.admin.service;

import com.kh.back.admin.dto.AdminCandidate;
import com.kh.back.admin.dto.AdminModelReport;
import com.kh.back.admin.dto.AdminModelReport.Epoch;
import com.kh.back.admin.dto.AdminModelReport.Metric;
import com.kh.back.admin.dto.AdminModelReport.SplitProfiles;
import com.kh.back.admin.dto.AdminModelReport.Version;
import com.kh.back.admin.mapper.AdminModelMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

/**
 * 학습 결과 파일은 조원(ML)이 git 에 올린 ml/outputs/models/... 를 읽기만 한다 (고치지 않음).
 * 폴더는 추천 서버(ml/serve-candidates.ps1)가 쓰는 기본 폴더와 같게 두고, 바뀌면 환경변수 ML_MODEL_RUN_DIR 로 바꾼다.
 */
@Slf4j
@Service
public class AdminModelServiceImpl implements AdminModelService {

    // 화면에 보일 지표 이름 (report.json comparison.metrics 의 키 → 이름)
    private static final List<String[]> METRICS = List.of(
            new String[] {"standalone_ndcg_at_3", "단독 NDCG@3"},
            new String[] {"final_ndcg_at_3", "최종 NDCG@3"},
            new String[] {"fuel_match_at_3", "연료 일치@3"});

    private final AdminModelMapper adminModelMapper;
    private final ObjectMapper objectMapper;
    private final String runDir;

    public AdminModelServiceImpl(AdminModelMapper adminModelMapper, ObjectMapper objectMapper,
                                 @Value("${admin.model-run-dir}") String runDir) {
        this.adminModelMapper = adminModelMapper;
        this.objectMapper = objectMapper;
        this.runDir = runDir;
    }

    @Override
    public AdminModelReport getReport() {
        List<Version> versions = adminModelMapper.findVersions().stream()
                .map(row -> new Version(row.getVersionLabel(), row.getExecutionType(), row.getCreatedAt(), row.getDiagnoses()))
                .toList();
        Path dir = findRunDir();
        if (dir == null) {
            return new AdminModelReport(false, null, null, null, null, null, null, null, null, null, null, null,
                    List.of(), List.of(), versions);
        }
        try {
            JsonNode report = read(dir.resolve("report.json"));
            JsonNode metadata = read(dir.resolve("metadata.json"));
            JsonNode holdout = Files.exists(dir.resolve("holdout_report.json")) ? read(dir.resolve("holdout_report.json")) : null;
            JsonNode generation = report.path("generation");
            JsonNode counts = generation.path("counts");

            List<Metric> metrics = new ArrayList<>();
            JsonNode compared = report.path("comparison").path("metrics");
            for (String[] metric : METRICS) {
                JsonNode current = compared.path("new").path(metric[0]);
                JsonNode previous = compared.path("old").path(metric[0]);
                if (current.isNumber() && previous.isNumber()) {
                    metrics.add(new Metric(metric[1], previous.asDouble(), current.asDouble()));
                }
            }
            List<Epoch> history = new ArrayList<>();
            for (JsonNode epoch : report.path("history")) {
                history.add(new Epoch(epoch.path("epoch").asInt(), epoch.path("loss").asDouble(),
                        epoch.path("validation_pair_accuracy").asDouble()));
            }
            LocalDateTime trainedAt = Files.exists(dir.resolve("model.pt"))
                    ? LocalDateTime.ofInstant(Files.getLastModifiedTime(dir.resolve("model.pt")).toInstant(), ZoneId.systemDefault())
                    : null;

            return new AdminModelReport(true, dir.getFileName().toString(), metadata.path("schema").asString(null), trainedAt,
                    longOrNull(generation.path("profiles")), longOrNull(generation.path("candidate_rows")),
                    longOrNull(generation.path("preference_pairs")),
                    new SplitProfiles(counts.path("train_profiles").asLong(), counts.path("validation_profiles").asLong(),
                            counts.path("test_profiles").asLong()),
                    generation.path("held_out_models").size(),
                    holdout == null ? null : holdout.path("test_pair_accuracy").asDouble(),
                    holdout == null ? null : holdout.path("financial_violations").asInt(),
                    holdout == null ? null : holdout.path("meaning").asString(null),
                    metrics, history, versions);
        } catch (Exception e) {
            // 파일 형식이 바뀌었거나 읽을 수 없음 → 화면에는 "학습 결과를 읽지 못함" (모델 버전 기록은 보여 준다)
            log.warn("admin model report: cannot read {}: {}", dir, e.getMessage());
            return new AdminModelReport(false, dir.getFileName().toString(), null, null, null, null, null, null, null, null,
                    null, null, List.of(), List.of(), versions);
        }
    }

    @Override
    public List<AdminCandidate> getCandidates() {
        Path dir = findRunDir();
        if (dir == null || !Files.exists(dir.resolve("catalog.json"))) {
            return List.of();
        }
        try {
            List<AdminCandidate> candidates = new ArrayList<>();
            for (JsonNode v : read(dir.resolve("catalog.json"))) {
                candidates.add(new AdminCandidate(v.path("id").asString(null), v.path("brand").asString(null),
                        v.path("model").asString(null), v.path("trim").asString(null), v.path("year").asString(null),
                        longOrNull(v.path("price")), v.path("fuel").asString(null),
                        v.path("efficiency").isNumber() ? v.path("efficiency").asDouble() : null,
                        v.path("length_mm").isNumber() ? v.path("length_mm").asInt() : null,
                        v.path("seats_label").asString(null), v.path("seats_status").asString(null),
                        v.path("seats_note").asString(null), v.path("source_url").asString(null),
                        v.path("checked_on").asString(null), v.path("quality").asString(null)));
            }
            return candidates;
        } catch (Exception e) {
            log.warn("admin candidates: cannot read {}: {}", dir, e.getMessage());
            return List.of();
        }
    }

    // 서버를 프로젝트 맨 위에서 켜도, back 폴더에서 켜도 찾게 두 곳을 본다 (dev.sh 는 back 에서 켬)
    private Path findRunDir() {
        for (Path candidate : List.of(Path.of(runDir), Path.of("..").resolve(runDir))) {
            if (Files.isDirectory(candidate) && Files.exists(candidate.resolve("report.json"))) {
                return candidate.toAbsolutePath().normalize();
            }
        }
        return null;
    }

    private JsonNode read(Path file) throws Exception {
        return objectMapper.readTree(Files.readString(file));
    }

    private static Long longOrNull(JsonNode node) {
        return node.isNumber() ? node.asLong() : null;
    }
}
