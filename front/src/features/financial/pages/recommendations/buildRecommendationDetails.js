const brands = {
  OWN001: '기아', OWN002: '기아', OWN003: '기아', OWN004: '기아', OWN005: '기아', OWN006: '기아', OWN007: '기아',
  OWN008: '르노코리아', OWN009: '현대', OWN010: '현대', OWN011: '현대', OWN012: '현대', OWN013: '현대', OWN014: '현대',
  OWN015: '테슬라', OWN016: '메르세데스-벤츠', OWN017: 'BMW', OWN018: '렉서스', OWN019: 'BMW', OWN020: '볼보',
};

// 차체·이용목적에 따른 참고 설명이다. 모델의 특성 기여도나 트림별 제원을 추정하지 않는다.
function purposeReason(body, purpose) {
  const spacious = ['SUV', 'RV', 'MPV', '승합', '미니밴'].includes(body);
  const compact = body === '경차';
  if (purpose === '가족 이동' && spacious) return '가족 이동에 사용할 후보로, 동승 인원과 짐을 고려해 실내·적재 공간을 살펴보기 좋은 차체입니다.';
  if (purpose === '주말 여가' && spacious) return '여가용 후보로, 여행 짐이나 야외 활동 장비를 싣는 공간을 살펴보기 좋은 차체입니다.';
  if (purpose === '출퇴근' && compact) return '출퇴근용 후보로, 작은 차체를 활용한 주차와 좁은 도로에서의 이동을 고려해 볼 수 있습니다.';
  if (purpose === '출퇴근' && body === '세단') return '출퇴근용 세단 후보로, 매일 주행할 경로에서의 승차감과 운전 편의성을 비교해 볼 수 있습니다.';
  if (purpose === '업무' && spacious) return '업무용 후보로, 동승자나 업무 물품을 위한 공간 활용을 비교해 볼 수 있습니다.';
  if (compact) return '작은 차체를 선호한다면 주차 공간과 주로 다니는 도로 환경을 기준으로 비교해 볼 수 있는 후보입니다.';
  if (body === '세단') return '세단을 선호한다면 탑승 공간과 승차감, 트렁크 활용도를 비교해 볼 수 있는 후보입니다.';
  if (spacious) return '공간 활용을 중시한다면 좌석 구성과 적재 공간을 비교해 볼 수 있는 후보입니다.';
  return '입력한 이용목적에 맞는지 탑승 공간과 실제 운행 조건을 함께 비교해 보세요.';
}

export function buildRecommendationDetails(vehicle, diagnosis, rank) {
  const purpose = diagnosis?.vehicle?.purpose;
  const distance = diagnosis?.vehicle?.annualDistance;
  const conditions = [purpose, distance && `연 ${distance}`].filter(Boolean).join(' · ');
  return {
    brand: brands[vehicle.labelCode] || '확인 필요',
    reasons: [
      { title: '진단 조건을 반영한 후보', description: `입력한 소득·생활비·자산·기존 대출${conditions ? `과 이용 조건(${conditions})` : ''}을 반영한 모델 추천 ${rank}위 차량입니다.` },
      { title: purpose ? `${purpose} 관점에서 살펴보기` : '차량 특징 살펴보기', description: purposeReason(vehicle.body, purpose) },
    ],
  };
}
