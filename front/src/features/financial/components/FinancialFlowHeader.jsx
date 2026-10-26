import '../styles/FinancialPages.css';

const steps = ['재무 정보', '차량 취향', '종합 분석', '추천 차량'];

export default function FinancialFlowHeader({ current, title, description }) {
  return <>
    <header className="financial-page-heading">
      <div><span className="financial-eyebrow">나에게 맞는 첫차 찾기</span><h1>{title}</h1><p>{description}</p></div>
      <span className="financial-stage-badge">{current} / {steps.length} · {steps[current - 1]}</span>
    </header>
    <nav className="financial-progress" aria-label="재무 진단 진행 단계">
      <ol>{steps.map((step, index) => <li key={step} className={current === index + 1 ? 'current' : current > index + 1 ? 'completed' : ''} aria-current={current === index + 1 ? 'step' : undefined}>{index + 1} {step}</li>)}</ol>
      <div className="financial-progress-track" aria-hidden="true"><span style={{ width: `${current / steps.length * 100}%` }} /></div>
    </nav>
  </>;
}
