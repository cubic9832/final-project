import VehicleTastePreview from './VehicleTastePreview.jsx';
import AccelerationPreview from './AccelerationPreview.jsx';

const choices = [
  ['exteriorAngularity', '차체의 선과 윤곽', [['any', '상관없음'], ['0', '둥글고 부드럽게'], ['0.5', '직선과 곡선의 조화'], ['1', '각지고 또렷하게']]],
  ['accelerationPreference', '원하는 가속 성능', [['any', '상관없음'], ['0', '완만한 가속'], ['0.5', '중간 수준'], ['1', '빠른 가속']]],
  ['lifestylePurpose', '주로 어떻게 이용하시나요?', [['any', '정해진 목적 없음'], ['commute', '출퇴근·도심 이동'], ['family', '가족과 함께 이동']]],
];
export default function LifestylePreferences({ value, onChange, includePurpose = true }) {
  const update = (name, next) => onChange(previous => ({ ...previous, [name]: next }));
  return <section aria-labelledby="lifestyle-title" className="vehicle-lifestyle">
    <h2 id="lifestyle-title">외관과 주행 감각</h2>
    <p className="vehicle-field-help">{includePurpose ? '마음에 드는 윤곽과 가속 성향, 주로 이용할 목적을 선택해 주세요.' : '마음에 드는 차체 윤곽과 원하는 가속 성향을 선택해 주세요.'}</p>
    {choices.filter(([name]) => includePurpose || name !== 'lifestylePurpose').map(([name, label, options]) => <fieldset className="vehicle-purpose" key={name}>
      <legend>{label}</legend>
      <div className="vehicle-purpose-options">{options.map(([option, text]) => <label key={option}>
        <input type="radio" name={name} value={option} checked={value[name] === option} onChange={() => update(name, option)} /><span>{text}</span>
      </label>)}</div>
      <VehicleTastePreview preference={name} value={value[name]} />
      {name === 'lifestylePurpose' && <p className="vehicle-field-help">도심 이동은 차량 크기를, 가족 이동은 탑승 인원을 함께 고려해요.</p>}
      {name === 'accelerationPreference' && <p className="vehicle-field-help">정지 상태에서 시속 100km까지 도달하는 시간을 비교해요.</p>}
      {name === 'accelerationPreference' && <AccelerationPreview value={value[name]} />}
    </fieldset>)}

  </section>;
}
