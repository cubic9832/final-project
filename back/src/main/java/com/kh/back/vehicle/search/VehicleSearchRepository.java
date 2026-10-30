package com.kh.back.vehicle.search;

import com.kh.back.common.exception.ApiException;
import co.elastic.clients.elasticsearch._types.query_dsl.Operator;
import co.elastic.clients.elasticsearch._types.query_dsl.TextQueryType;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DataAccessException;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.elasticsearch.client.elc.NativeQuery;
import org.springframework.data.elasticsearch.core.ElasticsearchOperations;
import org.springframework.data.elasticsearch.core.IndexOperations;
import org.springframework.data.elasticsearch.core.SearchHit;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;

/** ES vehicles 인덱스 접근. 색인을 통째로 다시 만들고, 검색어로 관련도 순 차량 id 를 찾는다. */
@Repository
@RequiredArgsConstructor
public class VehicleSearchRepository {
    // 화면이 사용자 조건으로 다시 거르므로, 전체 차량보다 넉넉하게 잡아 맞는 차는 모두 돌려준다
    private static final int MAX_RESULTS = 1000;
    private final ElasticsearchOperations operations;

    public void reindex(List<VehicleDocument> documents) {
        IndexOperations index = operations.indexOps(VehicleDocument.class);
        index.delete();
        index.createWithMapping();
        operations.save(documents);
        index.refresh();
    }

    public List<Long> searchIds(String keyword) {
        // 모든 단어가 어느 필드엔가 있어야 맞고("현대 하이브리드"), 입력 중인 차명·브랜드 앞부분("그랜")도 맞게 한다
        NativeQuery query = NativeQuery.builder()
                .withQuery(q -> q.bool(b -> b
                        .should(s -> s.multiMatch(m -> m.query(keyword)
                                .fields("name^3", "brand^2", "trimName", "powertrain", "classLabel^2", "fuelLabel^2", "conditionLabel")
                                .type(TextQueryType.CrossFields)
                                .operator(Operator.And)))
                        .should(s -> s.multiMatch(m -> m.query(keyword)
                                .fields("name.prefix^2", "brand.prefix")
                                .operator(Operator.And)))))
                .withPageable(PageRequest.of(0, MAX_RESULTS))
                .build();
        try {
            return operations.search(query, VehicleDocument.class).getSearchHits().stream()
                    .map(SearchHit::getContent)
                    .map(VehicleDocument::getId)
                    .toList();
        } catch (DataAccessException error) {
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "SEARCH_UNAVAILABLE", "검색 서버에 연결할 수 없습니다.");
        }
    }
}
