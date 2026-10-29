package com.kh.back.vehicle.search;

import com.kh.back.vehicle.mapper.VehicleMapper;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/**
 * 서버가 뜰 때 MySQL 차량을 ES 에 다시 색인한다. vehicles 는 Flyway 시드로만 바뀌어 시작할 때 한 번이면 충분하다.
 * ES 가 꺼져 있어도 서버는 계속 뜨고, 검색 요청만 503 으로 응답한다.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class VehicleSearchIndexer {
    private final VehicleMapper vehicleMapper;
    private final VehicleSearchRepository searchRepository;

    @EventListener(ApplicationReadyEvent.class)
    public void reindex() {
        try {
            List<VehicleDocument> documents = vehicleMapper.findAll().stream().map(VehicleDocument::from).toList();
            searchRepository.reindex(documents);
            log.info("차량 {}건을 Elasticsearch 에 색인했습니다.", documents.size());
        } catch (RuntimeException error) {
            log.warn("Elasticsearch 차량 색인을 건너뜁니다. 차량 검색은 ES 를 켠 뒤 서버를 다시 시작하면 동작합니다: {}", error.getMessage());
        }
    }
}
