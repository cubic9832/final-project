import './FinancialProfileFields.css';

const fields = [
  { name: 'age', label: '나이', unit: '세', min: 18, max: 100 },
  { name: 'career', label: '경력', unit: '년', min: 0, max: 80 },
  { name: 'householdSize', label: '가구원 수', unit: '명', min: 1, max: 30 },
  { name: 'dependents', label: '부양 인원', unit: '명', min: 0, max: 30 },
  { name: 'annualGrossIncome', label: '연간 세전소득', unit: '만 원/년', money: true },
  { name: 'averageSavings', label: '실제 월평균 저축액', unit: '만 원/월', money: true },
];
const categories = [
  { name: 'gender', label: '성별', options: ['남성', '여성'] },
  { name: 'employment', label: '직업 유형', options: ['근로자', '비취업', '자영업자', '프리랜서'] },
];

export default function FinancialProfileFields({ values, onChange }) {
  return <section className="financial-profile-fields" aria-labelledby="financial-profile-title">
    <h3 id="financial-profile-title">차량 추천에 필요한 기본 정보</h3>
    <p>연간 세전소득은 월 실수령액과 구분해 입력해 주세요. 실제 저축액은 위의 목표 저축액과 별개입니다.</p>
    <div className="financial-fields">{fields.map(({ name, label, unit, min = 0, max, money }) => <div className="financial-field" key={name}>
      <label htmlFor={`financial-${name}`}>{label}<span className="financial-required" aria-hidden="true"> *</span></label>
      <div className="financial-input-wrap"><input id={`financial-${name}`} name={name} type="number" min={min} max={max}
        step={money ? '0.01' : '1'} inputMode={money ? 'decimal' : 'numeric'} required value={values[name] ?? ''}
        onChange={(event) => onChange(name, event.target.value)} /><span aria-hidden="true">{unit}</span></div>
    </div>)}{categories.map(({ name, label, options }) => <div className="financial-field" key={name}>
      <label htmlFor={`financial-${name}`}>{label}<span className="financial-required" aria-hidden="true"> *</span></label>
      <select id={`financial-${name}`} name={name} required value={values[name] ?? ''} onChange={(event) => onChange(name, event.target.value)}>
        <option value="">선택해 주세요</option>{options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </div>)}</div>
  </section>;
}
