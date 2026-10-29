
const choices = [
  ['exteriorSportiness', '마음에 드는 외관 디자인', [['any', '상관없음'], ['0', '크고 무거운 디자인'], ['0.5', '균형 잡힌 디자인'], ['1', '빠르고 날렵한 디자인']]],
  ['exteriorAngularity', '차체의 선과 윤곽', [['any', '상관없음'], ['0', '둥글고 부드럽게'], ['0.5', '직선과 곡선의 조화'], ['1', '각지고 또렷하게']]],
  ['accelerationPreference', '원하는 가속 성능', [['any', '상관없음'], ['0.5', '중간 수준'], ['1', '빠른 가속']]],
  ['lifestylePurpose', '주로 어떻게 이용하시나요?', [['any', '정해진 목적 없음'], ['commute', '출퇴근·도심 이동'], ['family', '가족과 함께 이동']]],
];
const priorities = [
  ['designImportance', '디자인', value => value.exteriorSportiness === 'any' && value.exteriorAngularity === 'any'],
  ['lifestylePurposeImportance', '사용 목적', value => value.lifestylePurpose === 'any'],
  ['performanceImportance', '가속 성능', value => value.accelerationPreference === 'any'],
];

export default function LifestylePreferences({ value, onChange }) {
  const update = (name, next) => onChange(previous => ({ ...previous, [name]: next }));
  return <section aria-labelledby="lifestyle-title" className="vehicle-lifestyle">
    <h3 id="lifestyle-title">예산 안에서, 마음에 드는 차</h3>
    <p className="vehicle-field-help">마음에 드는 스타일과 주로 이용할 목적을 선택해 주세요.</p>
    {choices.map(([name, label, options]) => <fieldset className="vehicle-purpose" key={name}>
      <legend>{label}</legend>
      <div className="vehicle-purpose-options">{options.map(([option, text]) => <label key={option}>
        <input type="radio" name={name} value={option} checked={value[name] === option} onChange={() => update(name, option)} /><span>{text}</span>
      </label>)}</div>
      {name === 'lifestylePurpose' && <p className="vehicle-field-help">도심 이동은 차량 크기를, 가족 이동은 탑승 인원을 함께 고려해요.</p>}
      {name === 'accelerationPreference' && <p className="vehicle-field-help">정지 상태에서 시속 100km까지 도달하는 시간을 기준으로 비교해요.</p>}
    </fieldset>)}
    <fieldset className="vehicle-preferences"><legend>내 취향의 중요도</legend>
      <div className="vehicle-priority-list">{priorities.map(([name, label, inactive]) => <fieldset className="vehicle-priority-row" key={name} disabled={inactive(value)}>
        <legend>{label}{inactive(value) && <small>취향을 선택하면 설정할 수 있어요</small>}</legend>
        <div className="vehicle-purpose-options">{[['1', '낮음'], ['3', '중간'], ['5', '높음']].map(([option, text]) => <label key={option}>
          <input type="radio" name={name} value={option} checked={value[name] === option} onChange={() => update(name, option)} /><span>{text}</span>
        </label>)}</div>
      </fieldset>)}</div>
    </fieldset>
  </section>;
}
