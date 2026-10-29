export default function ScenarioPreferences({ value, onChange }) {
  const update = (name, next) => onChange(previous => ({ ...previous, [name]: next }));
  return <section className="vehicle-lifestyle" aria-labelledby="scenario-title">
    <h3 id="scenario-title">차를 이용하는 환경과 비용 성향</h3>
    <div className="vehicle-fields">
      <div className="financial-field"><label htmlFor="scenario-distance">연간 주행거리</label>
        <select id="scenario-distance" value={value.annualDistanceKm ?? '15000'} onChange={event => update('annualDistanceKm', event.target.value)}>
          {[5000, 10000, 15000, 20000, 30000, 50000].map(distance => <option key={distance} value={distance}>{distance.toLocaleString('ko-KR')}km</option>)}
        </select></div>
    </div>
    <fieldset className="vehicle-purpose"><legend>집이나 직장에서 꾸준히 충전할 수 있나요?</legend>
      <div className="vehicle-purpose-options">{[[false, '충전 여건 없음'], [true, '충전 가능']].map(([available, label]) => <label key={String(available)}>
        <input type="radio" name="scenario-charging" checked={(value.chargingAvailable ?? false) === available} onChange={() => update('chargingAvailable', available)} /><span>{label}</span>
      </label>)}</div>
    </fieldset>
    <div className="vehicle-priority-list">{[['costImportance', '구매비·유지비']].map(([name, label]) => <fieldset className="vehicle-priority-row" key={name}>
      <legend>{label} 중요도</legend><div className="vehicle-purpose-options">{[['1', '낮음'], ['3', '중간'], ['5', '높음']].map(([option, text]) => <label key={option}>
        <input type="radio" name={name} checked={String(value[name] ?? '3') === option} onChange={() => update(name, option)} /><span>{text}</span>
      </label>)}</div>
    </fieldset>)}</div>
  </section>;
}
