import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { getRecommendationOptions, getRecommendations } from '../../recommendationApi.js';
import { categoryFields, emptyProfile, numericFields, profileGroups, toModelProfile, validateProfile } from './profileFields.js';
import RecommendationResults from './RecommendationResults.jsx';
import './PredictPage.css';

const example = {
  '나이_세': 27, '경력_년': 5, '가구원수_명': 4, '부양인원_명': 1,
  '개인_연간세전소득_원': 7961.7, '개인_평균월주거비_원': 85.8,
  '개인_평균월기타생활소비_원': 195.7, '개인_평균월저축액_원': 156.6,
  '개인_현금성자산_원': 1774.2, '개인_기타금융자산_원': 992,
  '개인_주거보증금자산_원': 0, '개인_부동산자산_원': 0,
  '기존대출잔액_보정전_원': 0, '연간_주행거리_km': 10529,
  '성별': '남성', '직업_유형': '근로자', '차량_이용목적': '여가',
};

export default function PredictPage() {
  const [segment, setSegment] = useState('domestic-car');
  const [values, setValues] = useState({ ...emptyProfile });
  const [segments, setSegments] = useState([]);
  const [optionsState, setOptionsState] = useState('loading');
  const [attempt, setAttempt] = useState(0);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState(null);
  const activeRequest = useRef(null);
  const selected = segments.find((item) => item.code === segment);

  useEffect(() => {
    const controller = new AbortController();
    getRecommendationOptions(controller.signal).then((data) => {
      if (controller.signal.aborted) return;
      setSegments(data);
      setOptionsState('ready');
    }).catch(() => {
      if (!controller.signal.aborted) setOptionsState('error');
    });
    return () => controller.abort();
  }, [attempt]);

  useEffect(() => () => activeRequest.current?.abort(), []);

  function retryOptions() {
    setOptionsState('loading');
    setAttempt((value) => value + 1);
  }

  function change(key, value) {
    setValues((previous) => ({ ...previous, [key]: value }));
    setErrors((previous) => ({ ...previous, [key]: undefined }));
    setResult(null);
    setMessage('');
  }

  function changeSegment(value) {
    setSegment(value);
    setValues((previous) => ({ ...previous, ...Object.fromEntries(categoryFields.map(({ key }) => [key, ''])) }));
    setErrors({});
    setResult(null);
    setMessage('');
  }

  function fillExample() {
    setValues({ ...example, ...Object.fromEntries(categoryFields.map(({ key }) => {
      const options = selected?.categories[key] ?? [];
      return [key, options.includes(example[key]) ? example[key] : options[0] ?? ''];
    })) });
    setErrors({});
    setResult(null);
    setMessage('예시 조건을 채웠습니다. 내 조건으로 수정한 뒤 추천받을 수 있습니다.');
  }

  async function submit(event) {
    event.preventDefault();
    if (activeRequest.current || !selected?.available) return;
    const validation = validateProfile(values);
    setErrors(validation);
    setMessage('');
    if (Object.keys(validation).length) {
      event.currentTarget.elements.namedItem(Object.keys(validation)[0])?.focus();
      return;
    }
    const controller = new AbortController();
    activeRequest.current = controller;
    setPending(true);
    setResult(null);
    try {
      const response = await getRecommendations(segment, toModelProfile(values), controller.signal);
      setResult(response);
    } catch (error) {
      if (!controller.signal.aborted) {
        const problem = error.response?.data;
        setMessage(problem?.detail ?? '추천 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.');
        const fields = [...numericFields, ...categoryFields];
        setErrors(Object.fromEntries((problem?.errors ?? []).filter(({ field }) => fields.some(({ key }) => key === field))
          .map(({ field, message: detail }) => [field, detail])));
      }
    } finally {
      activeRequest.current = null;
      if (!controller.signal.aborted) setPending(false);
    }
  }

  return <div className="recommendation-page">
    <header className="recommendation-heading"><span className="recommendation-eyebrow">차량 추천</span>
      <h1>내 조건으로 차량 추천받기</h1><p>구매 전 재무정보와 이용목적을 바탕으로 차량 후보를 찾아보세요.</p></header>
    <aside className="recommendation-intro"><strong>입력 기준을 확인해 주세요</strong>
      <p>소득은 연간 세전소득, 지출은 월 기준입니다. 금액은 만 원 단위로 입력하며, 기존 대출에는 새 차량 할부를 포함하지 않습니다.</p>
      <p>합성 데이터로 학습한 참고 추천입니다. 차량 가격·월 부담·구매 가능 여부는 <Link to="/financial">재무 진단</Link>에서 별도로 확인해 주세요.</p>
    </aside>
    {optionsState === 'loading' && <p className="recommendation-card" role="status">추천 서비스를 확인하고 있습니다.</p>}
    {optionsState === 'error' && <div className="recommendation-card" role="alert"><p>추천 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.</p>
      <button type="button" className="recommendation-secondary" onClick={retryOptions}>다시 연결하기</button></div>}
    {optionsState === 'ready' && <form onSubmit={submit} noValidate>
      <fieldset disabled={pending} className="recommendation-form">
        <legend className="recommendation-sr-only">차량 추천 조건</legend>
        <section className="recommendation-card recommendation-segment"><div><h2>차량 구분</h2><p>추천받을 차량을 선택해 주세요.</p></div>
          <div className="recommendation-segment-buttons">{segments.map((item) => <button key={item.code} type="button"
            aria-pressed={segment === item.code} onClick={() => changeSegment(item.code)}>{item.label}</button>)}</div>
          <button type="button" className="recommendation-secondary" onClick={fillExample} disabled={!selected?.available}>예시 조건 채우기</button>
        </section>
        {!selected?.available && <div className="recommendation-service-error" role="alert"><p>선택한 차량 구분은 현재 추천할 수 없습니다. 다른 구분을 선택하거나 잠시 후 다시 시도해 주세요.</p><button type="button" className="recommendation-secondary" onClick={retryOptions}>다시 확인하기</button></div>}
        {profileGroups.map((group) => <section className="recommendation-card" key={group.title}><h2>{group.title}</h2>
          <div className="recommendation-fields">{group.fields.map((field) => <div className="recommendation-field" key={field.key}>
            <label htmlFor={`profile-${field.key}`}>{field.label}<span className="recommendation-required"> 필수</span></label>
            <div className="recommendation-input"><input id={`profile-${field.key}`} name={field.key} type="number" inputMode={field.scale ? 'decimal' : 'numeric'}
              min={field.min ?? 0} max={field.max} step={field.scale ? '0.01' : '1'} value={values[field.key]}
              onChange={(event) => change(field.key, event.target.value)} required aria-invalid={Boolean(errors[field.key])}
              aria-describedby={errors[field.key] ? `error-${field.key}` : undefined} /><span>{field.unit}</span></div>
            {errors[field.key] && <p className="recommendation-field-error" id={`error-${field.key}`}>{errors[field.key]}</p>}
          </div>)}</div>
          {group.title === '차량 이용 조건' && <div className="recommendation-fields">{categoryFields.map((field) => <div className="recommendation-field" key={field.key}>
            <label htmlFor={`profile-${field.key}`}>{field.label}<span className="recommendation-required"> 필수</span></label>
            <select id={`profile-${field.key}`} name={field.key} value={values[field.key]} onChange={(event) => change(field.key, event.target.value)}
              required aria-invalid={Boolean(errors[field.key])} aria-describedby={errors[field.key] ? `error-${field.key}` : undefined}>
              <option value="">선택해 주세요</option>{(selected?.categories[field.key] ?? []).map((option) => <option key={option}>{option}</option>)}</select>
            {errors[field.key] && <p className="recommendation-field-error" id={`error-${field.key}`}>{errors[field.key]}</p>}
          </div>)}</div>}
        </section>)}
        <div className="recommendation-submit"><p>입력한 조건은 추천 요청에만 사용하며 이 화면에서 저장하지 않습니다.</p>
          <button className="recommendation-primary" type="submit" disabled={!selected?.available || pending}>{pending ? '차량을 추천하고 있습니다…' : '차량 3대 추천받기'}</button></div>
      </fieldset>
    </form>}
    <p className="recommendation-message" role="status" aria-live="polite">{message}</p>
    <div aria-live="polite" aria-busy={pending}>{pending ? <p className="recommendation-card" role="status">입력 조건에 맞춰 차량 후보를 확인하고 있습니다.</p> : <RecommendationResults result={result} />}</div>
  </div>;
}
