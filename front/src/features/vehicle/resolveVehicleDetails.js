import details from './newVehicleDetails.json' with { type: 'json' };

const specificationsById = new Map(details.vehicles.map(vehicle => [vehicle.id, vehicle]));

export function resolveVehicleDetails(vehicle) {
  const specifications = specificationsById.get(vehicle.id);
  if (!specifications || ['brand', 'model', 'trim', 'year'].some(key =>
    String(specifications[key] ?? '') !== String(vehicle[key] ?? ''))) return undefined;
  return specifications;
}

const labels = {
  Length: '전장', Width: '전폭 (미러 제외)', 'Width (with mirrors)': '전폭 (미러 포함)',
  Wheelbase: '휠베이스', 'Height (PASM)': '전고 (PASM)',
  'Height (PASM Sport Suspension)': '전고 (PASM 스포츠 서스펜션)',
  'Height, steel suspension (PASM DIN)': '전고 (PASM DIN)',
  'Height (PASM -10 DIN)': '전고 (PASM -10 DIN)', 'Height (PASM -20 DIN)': '전고 (PASM -20 DIN)',
  Displacement: '배기량', 'Number of cylinders': '실린더 수',
  'Power combined (PS)': '시스템 합산 출력 (PS)', 'Power combined (kW)': '시스템 합산 출력 (kW)',
  'Power (PS)': '엔진 출력 (PS)', 'Power (kW)': '엔진 출력 (kW)',
  'Max. torque': '엔진 최대 토크', 'Torque combined': '시스템 합산 토크',
  Transmission: '변속기', 'Top speed': '최고 속도',
  'Acceleration 0 - 100 km/h': '0–100 km/h',
  'Acceleration 0 - 100 km/h with Sport Chrono Package': '0–100 km/h (스포츠 크로노 패키지)',
  'Luggage compartment volume, front': '앞 트렁크 용량',
  'Open luggage compartment volume (behind front seats)': '앞좌석 뒤 적재 공간',
  'Maximum load': '최대 적재중량', 'Turning circle': '회전 직경',
};

export function specificationLabel(label) {
  return labels[label] ?? label;
}
