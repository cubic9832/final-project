import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import vehiclePhoto from '../../../../assets/vehicles/vehicle-0.webp';
import useAuthStore from '../../../../stores/useAuthStore';
import { getTasteCatalog, getCurrentTaste, putCurrentTaste, tasteErrorMessage } from '../../tasteApi';
import { isCurrentTasteSaved, resolveTaste, savedTasteAnswers } from '../../serverTasteFlow';
import { readMemberTasteDraft, writeMemberTasteDraft } from '../../tasteDraftStorage';
import TasteQuestion from './TasteQuestion';
import TasteResult from './TasteResult';
import TasteSaveModal from './TasteSaveModal';
import './TasteTestPage.css';

export default function TasteTestPage() {
  const memberId = useAuthStore((state) => state.member?.id);
  const [catalog, setCatalog] = useState(null);
  const [current, setCurrent] = useState(null);
  const [draft, setDraft] = useState(null);
  const [confirmation, setConfirmation] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const saving = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([getTasteCatalog(controller.signal), getCurrentTaste(controller.signal)])
      .then(([bank, stored]) => {
        if (controller.signal.aborted) return;
        setCatalog(bank);
        setCurrent(stored);
        setConfirmation(false);
        setDraft(readMemberTasteDraft(memberId, bank)
          ?? { phase: 'intro', step: 0, answers: Array(bank.questionCount).fill(null) });
      })
      .catch((failure) => { if (!controller.signal.aborted) setError(tasteErrorMessage(failure)); });
    return () => controller.abort();
  }, [memberId, reload]);

  useEffect(() => {
    if (catalog && draft) writeMemberTasteDraft(memberId, catalog.version, draft);
  }, [memberId, catalog, draft]);

  if (!catalog || !draft) return <section className="taste-page taste-card">
    {error ? <><p role="alert">{error}</p><button type="button" className="taste-button taste-button-outline" onClick={() => { setError(''); setReload((value) => value + 1); }}>다시 시도</button></>
      : <p role="status">취향 테스트를 준비하고 있어요.</p>}
  </section>;

  const flow = resolveTaste(catalog, draft.answers);
  const result = draft.phase === 'result' ? flow.result : null;
  const saved = result !== null && isCurrentTasteSaved(catalog, draft.answers, current);

  function restart() {
    setNotice(''); setError('');
    setDraft({ phase: 'question', step: 0, answers: Array(catalog.questionCount).fill(null) });
  }
  function next() {
    if (draft.answers[draft.step] === null) return;
    setDraft((value) => value.step < catalog.questionCount - 1
      ? { ...value, step: value.step + 1 } : { ...value, phase: 'result' });
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  async function persist() {
    if (saving.current || saved) return;
    saving.current = true; setBusy(true); setError('');
    try {
      const record = await putCurrentTaste({ version: catalog.version, expectedSavedAt: current?.savedAt ?? null,
        answers: flow.path.map((question, step) => ({ questionId: question.id, optionId: question.options[draft.answers[step]].id })) });
      setCurrent(record); setConfirmation(false); setNotice('회원님의 현재 취향을 저장했어요.');
    } catch (failure) {
      setError(tasteErrorMessage(failure)); setNotice(tasteErrorMessage(failure));
    } finally { saving.current = false; setBusy(false); }
  }
  function requestSave() {
    if (saving.current || saved) return;
    setError('');
    if (current) setConfirmation(true);
    else persist();
  }
  function showCurrent() {
    const answers = savedTasteAnswers(catalog, current);
    if (!answers) { setNotice('이전 버전의 취향이에요. 새 테스트로 현재 취향을 확인해 주세요.'); return; }
    setDraft({ phase: 'result', step: catalog.questionCount - 1, answers }); setNotice('');
  }

  return <div className="taste-page">
    <nav className="taste-breadcrumb" aria-label="현재 위치"><Link to="/mypage">마이페이지</Link><span aria-hidden="true">/</span><span aria-current="page">첫 차 취향 테스트</span></nav>
    {draft.phase === 'intro' && <>
      <h1 className="taste-page-title">내 첫 자동차 취향 알아보기</h1>
      <section className="taste-intro taste-card">
        <p className="taste-eyebrow">8가지 질문으로 발견하는 나의 첫 차 취향</p>
        <img src={vehiclePhoto} alt="흰색 현대 아반떼 준중형 세단" width="1200" height="510" fetchPriority="high" />
        <h2>나의 첫 자동차,<br />어떤 차가 어울릴까요?</h2>
        <p>첫 차와 함께하고 싶은 일상을 떠올려보세요.<br />선택한 답에 따라 다음 질문이 달라져요.</p>
        <p className="taste-caption">8문항 · 약 2~3분 · 선택 사항</p>
        <div className="taste-actions">
          <button type="button" className="taste-button taste-button-outline" onClick={() => navigate('/')}>나중에 하기</button>
          <button type="button" className="taste-button taste-button-cta" onClick={restart}>취향 테스트 시작</button>
        </div>
        {current && <p>현재 취향 · {catalog.types[current.primary]?.name ?? current.primary} <button type="button" className="taste-button taste-button-outline" onClick={showCurrent}>저장한 취향 보기</button></p>}
      </section>
    </>}
    {draft.phase === 'question' && <TasteQuestion step={draft.step} answers={draft.answers}
      question={flow.path[draft.step]} questionCount={catalog.questionCount}
      onSelect={(answer) => {
        setDraft((value) => ({ ...value, answers: value.answers[value.step] === answer ? value.answers
          : value.answers.map((item, index) => index < value.step ? item : index === value.step ? answer : null) }));
      }}
      onPrevious={() => setDraft((value) => value.step === 0 ? { ...value, phase: 'intro' } : { ...value, step: value.step - 1 })}
      onNext={next} />}
    {result && <TasteResult result={result} types={catalog.types} onSave={requestSave} onRestart={restart} saved={saved} busy={busy} notice={notice} />}
    {draft.phase !== 'result' && notice && <p role="status">{notice}</p>}
    {result && confirmation && <TasteSaveModal previous={current.primary} next={result.primary} types={catalog.types} error={error} busy={busy}
      onClose={() => { if (!busy) { setConfirmation(false); setError(''); } }} onSave={persist} />}
  </div>;
}
