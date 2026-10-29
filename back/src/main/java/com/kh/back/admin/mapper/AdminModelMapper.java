package com.kh.back.admin.mapper;

import com.kh.back.admin.dto.ModelVersionRow;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;

// 7단계: 모델 버전 기록 (V1 model_versions — 재무 진단을 저장할 때 처음 보는 버전이 등록된다)
@Mapper
public interface AdminModelMapper {

    // 최근 등록 순 + 버전별 재무 진단 수
    List<ModelVersionRow> findVersions();
}
