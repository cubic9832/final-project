import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import vehiclePhoto from '../../assets/vehicles/vehicle-0.webp';
import useAuthStore from '../../stores/useAuthStore';
import { TASTE_QUESTION_COUNT } from './tasteQuestions';
import { emptyTasteAnswers, selectTasteAnswer } from './tasteFlow';
import { calculateTasteResult } from './calculateTasteResult';
import { readTasteDraft, writeTasteDraft, readCurrentTaste, saveCurrentTaste } from './tasteStorage';
import TasteQuestion from './TasteQuestion';
import TasteResult from './TasteResult';
import TasteSaveModal from './TasteSaveModal';
import './TasteTestPage.css';

export default function TasteTestPage() {
  const [draft, setDraft] = useState(() => readTasteDraft() ?? { phase: 'intro', step: 0, answers: emptyTasteAnswers() });
  const [confirmation, setConfirmation] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [saved, setSaved] = useState(false);
  const member = useAuthStore((state) => state.member);
  const navigate = useNavigate();
  const result = draft.phase === 'result' ? calculateTasteResult(draft.answers) : null;

  useEffect(() => { writeTasteDraft(draft); }, [draft]);

  function restart() {
    setSaved(false);
    setNotice('');
    setError('');
    setDraft({ phase: 'question', step: 0, answers: emptyTasteAnswers() });
  }
  function next() {
    if (draft.answers[draft.step] === null) return;
    if (draft.step < TASTE_QUESTION_COUNT - 1) {
      setDraft((value) => ({ ...value, step: value.step + 1 }));
    } else {
      const missing = draft.answers.indexOf(null);
      setDraft((value) => missing < 0 ? { ...value, phase: 'result' } : { ...value, step: missing });
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  }
  function persist() {
    try {
      saveCurrentTaste(member?.id, draft.answers);
      setConfirmation(null);
      setSaved(true);
      setError('');
      setNotice('현재 취향을 이 브라우저에 저장했어요. 다른 기기에는 반영되지 않습니다.');
    } catch {
      const message = '저장하지 못했어요. 브라우저 저장소 설정을 확인하고 다시 시도해주세요.';
      setError(message);
      setNotice(message);
    }
  }
  function requestSave() {
    setError('');
    if (member?.id == null) {
      writeTasteDraft(draft);
      navigate('/login', { state: { from: '/taste-test' } });
      return;
    }
    const previous = readCurrentTaste(member.id);
    if (previous) setConfirmation(calculateTasteResult(previous.answers).primary);
    else persist();
  }

  return (
    <div className="taste-page">
      <nav className="taste-breadcrumb" aria-label="현재 위치"><Link to="/">홈</Link><span aria-hidden="true">/</span><span>자동차 알아보기</span><span aria-hidden="true">/</span><span aria-current="page">취향 테스트</span></nav>
      {draft.phase === 'intro' && <>
        <h1 className="taste-page-title">내 첫 자동차 취향 알아보기</h1>
        <section className="taste-intro taste-card">
          <p className="taste-eyebrow">8가지 질문으로 발견하는 나의 첫 차 취향</p>
          <img src={vehiclePhoto} alt="일상에 어울리는 흰색 현대 아반떼 준중형 세단" width="1200" height="510" fetchPriority="high" />
          <h2>나의 첫 자동차,<br />어떤 차가 어울릴까요?</h2>
          <p>첫 차와 함께하고 싶은 일상을 떠올려보세요.<br />선택한 답에 따라 다음 질문이 달라져요.</p>
          <p className="taste-caption">8문항 · 문항별 1개 선택 · 약 2~3분 예상</p>
          <button type="button" className="taste-button taste-button-cta" onClick={() => setDraft((value) => ({ ...value, phase: 'question' }))}>내 첫 자동차 취향 알아보기</button>
        </section>
      </>}
      {draft.phase === 'question' && <TasteQuestion step={draft.step} answers={draft.answers}
        onSelect={(answer) => setDraft((value) => ({ ...value, answers: selectTasteAnswer(value.answers, value.step, answer) }))}
        onPrevious={() => setDraft((value) => value.step === 0 ? { ...value, phase: 'intro' } : { ...value, step: value.step - 1 })} onNext={next} />}
      {result && <TasteResult result={result} onSave={requestSave} onRestart={restart} saved={saved} notice={notice} />}
      {result && confirmation && <TasteSaveModal previous={confirmation} next={result.primary} error={error}
        onClose={() => { setConfirmation(null); setError(''); }} onSave={persist} />}
    </div>
  );
}
