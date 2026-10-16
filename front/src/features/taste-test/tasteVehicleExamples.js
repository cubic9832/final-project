import avanteImage from '../../assets/vehicles/vehicle-0.webp';

// 대표 모델 예시와 제조사 공식 이미지. 매물 추천이나 구매 가능 판정과는 분리한다.
const kiaImage = (path) => `https://www.kia.com/content/dam/kwp/kr/ko/vehicles/represent/${path}`;
const vehicles = {
  morning: { name: '기아 모닝', category: '경차', image: kiaImage('krja305/morning_jajh5ad3b_a_ud.png') },
  ray: { name: '기아 레이', category: '경차', image: kiaImage('krtm311/ray_tmjc5ah3i_a_ud.png') },
  avante: { name: '현대 아반떼', category: '준중형 세단', image: avanteImage },
  k5: { name: '기아 K5', category: '중형 세단', image: kiaImage('krdl308/k5_dljs49f38_h_swp.png') },
  sportage: { name: '기아 스포티지', category: 'SUV', image: kiaImage('krnq327/sportage_nqjj5ab37_a_swp.png') },
  sorento: { name: '기아 쏘렌토', category: 'SUV', image: kiaImage('krmq326/sorento_mqjj5acd8_a_agt.png') },
  carnival: { name: '기아 카니발', category: '미니밴', image: kiaImage('krkp328/carnival_kpjg99b39_a_swp.png') },
  ev3: { name: '기아 EV3', category: '전기 SUV', image: kiaImage('krsv292/ev3_svjj5vd33_a_swp.png') },
};

export const tasteVehicleExamples = {
  city: [vehicles.morning, vehicles.ray],
  comfort: [vehicles.avante, vehicles.k5],
  adventure: [vehicles.sportage, vehicles.sorento],
  together: [vehicles.sorento, vehicles.carnival],
  explorer: [vehicles.k5, vehicles.ev3],
};
