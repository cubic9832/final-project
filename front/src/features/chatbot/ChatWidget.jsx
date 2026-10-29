import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { Compass, Car, ClipboardList, BookOpen, ChevronRight, Info, X, Send, RotateCcw } from 'lucide-react';
import theme from '../../styles/theme';
import { sendChatMessage, sendChatGuide, getChatHistory, clearChatHistory } from './chatApi';
import useChatStore from './useChatStore';
import './ChatWidget.css';

const categories = [
  { id: 'service', label: '서비스 이용', Icon: ClipboardList, questions: [
    { title: '서비스를 어떻게 이용하나요?', guideId: 'service-overview' },
    { title: '취향 테스트 결과는 어떻게 저장하나요?', guideId: 'taste-save' },
    { title: '차량을 비교하려면 어떻게 하나요?', guideId: 'vehicle-compare' },
  ] },
  { id: 'body', label: '차종 도감', Icon: Car, questions: [
    { title: 'MPV는 어떤 차인가요?', guideId: 'MPV' },
    { title: '중형 SUV는 어떤 차인가요?', guideId: 'MIDSIZE_SUV' },
    { title: '세단과 SUV는 어떻게 다른가요?', guideId: 'sedan-suv' },
  ] },
  { id: 'terms', label: '자동차 용어', Icon: BookOpen, questions: [
    { title: '하이브리드는 무엇인가요?', guideId: 'hybrid-electric' },
    { title: '복합연비는 무슨 뜻인가요?', guideId: 'EFFICIENCY' },
    { title: 'PHEV와 일반 하이브리드는 다른가요?', guideId: 'PHEV' },
  ] },
];

export default function ChatWidget() {
  const open = useChatStore((state) => state.open);
  const setOpen = useChatStore((state) => state.setOpen);
  const questionRequest = useChatStore((state) => state.questionRequest);
  const consumeQuestion = useChatStore((state) => state.consumeQuestion);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [categoryId, setCategoryId] = useState('service');
  const [remaining, setRemaining] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [showUsageInfo, setShowUsageInfo] = useState(false);
  const category = categories.find((item) => item.id === categoryId);
  const panel = useRef(null);
  const trigger = useRef(null);
  const input = useRef(null);
  const bottom = useRef(null);
  const activeRequest = useRef(null);
  const mounted = useRef(false);
  const returnFocus = useRef(null);
  const usageInfo = useRef(null);
  const usageTrigger = useRef(null);

  useEffect(() => {
    if (!showUsageInfo || !open) return;
    const dismiss = (event) => {
      if (!usageInfo.current?.contains(event.target)) setShowUsageInfo(false);
    };
    const escape = (event) => {
      if (event.key !== 'Escape') return;
      event.stopImmediatePropagation();
      setShowUsageInfo(false);
      usageTrigger.current?.focus();
    };
    document.addEventListener('pointerdown', dismiss);
    document.addEventListener('keydown', escape, true);
    return () => {
      document.removeEventListener('pointerdown', dismiss);
      document.removeEventListener('keydown', escape, true);
    };
  }, [showUsageInfo, open]);

  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    getChatHistory(controller.signal).then((result) => {
      if (!mounted.current) return;
      setMessages(result.messages); setRemaining(result.remaining); setLoaded(true);
    }).catch((failure) => {
      if (!controller.signal.aborted) setError(failure.response?.data?.error?.message || '대화 기록을 불러오지 못했습니다.');
    });
    return () => { mounted.current = false; controller.abort(); activeRequest.current?.abort(); };
  }, []);

  async function reloadHistory() {
    if (activeRequest.current) return;
    setPending(true); setError('');
    try {
      const result = await getChatHistory();
      if (mounted.current) { setMessages(result.messages); setRemaining(result.remaining); setLoaded(true); }
    } catch (failure) {
      if (mounted.current) setError(failure.response?.data?.error?.message || '대화 기록을 불러오지 못했습니다.');
    } finally { if (mounted.current) setPending(false); }
  }

  async function resetConversation() {
    if (pending || activeRequest.current) return;
    setPending(true); setError('');
    try {
      await clearChatHistory();
      if (mounted.current) { setMessages([]); setDraft(''); input.current?.focus(); }
    } catch (failure) {
      if (mounted.current) setError(failure.response?.data?.error?.message || '대화를 지우지 못했습니다.');
    } finally { if (mounted.current) setPending(false); }
  }

  useEffect(() => {
    if (!open) return;
    input.current?.focus();
    const closeOutside = (event) => {
      if (!panel.current?.contains(event.target) && !trigger.current?.contains(event.target)) {
        setOpen(false);
      }
    };
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') {
        setOpen(false);
        (returnFocus.current?.isConnected ? returnFocus.current : trigger.current)?.focus();
      }
    };
    document.addEventListener('pointerdown', closeOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open, setOpen]);

  useEffect(() => {
    if (open && (messages.length > 0 || pending || error)) bottom.current?.scrollIntoView({ block: 'nearest' });
  }, [messages, pending, error, open]);

  async function send(text = draft, guideId = null) {
    const question = text.trim();
    if (!question || question.length > 500 || activeRequest.current || pending || !loaded || (!guideId && remaining === 0)) return;
    const controller = new AbortController();
    activeRequest.current = controller;
    setPending(true);
    setError('');
    if (!guideId) setDraft('');
    try {
      const result = guideId ? await sendChatGuide(guideId, controller.signal)
        : await sendChatMessage(question, controller.signal);
      if (!mounted.current) return;
      setRemaining(result.remaining);
      setMessages([...messages.slice(-8), { role: 'user', text: result.question },
        { role: 'model', text: result.answer }]);
    } catch (failure) {
      if (mounted.current) {
        setMessages(messages);
        if (!guideId) setDraft(question);
        setError(controller.signal.aborted ? '답변 요청을 취소했습니다. 질문을 다시 보낼 수 있습니다.'
          : failure.response?.data?.error?.message || '답변을 불러오지 못했습니다. 다시 보내 주세요.');
        if (failure.response?.data?.error?.code === 'CHAT_DAILY_LIMIT') setRemaining(0);
        else getChatHistory().then((result) => { if (mounted.current) setRemaining(result.remaining); }).catch(() => {});
      }
    } finally {
      activeRequest.current = null;
      if (mounted.current) setPending(false);
    }
  }

  const sendExplanation = useEffectEvent((request) => { void send(request.label, request.guideId); });
  useEffect(() => {
    if (!questionRequest || pending || !loaded) return;
    let cancelled = false;
    // A term click is an external request; defer until this committed view is ready.
    queueMicrotask(() => {
      if (cancelled || activeRequest.current) return;
      returnFocus.current = questionRequest.returnFocus;
      consumeQuestion(questionRequest.id);
      sendExplanation(questionRequest);
    });
    return () => { cancelled = true; };
  }, [questionRequest, pending, loaded, consumeQuestion]);

  function close() {
    setShowUsageInfo(false);
    setOpen(false);
    (returnFocus.current?.isConnected ? returnFocus.current : trigger.current)?.focus();
  }

  return (
    <div className="chat-widget">
      {open && (
        <section className="chat-panel" id="chat-panel" ref={panel} role="region" aria-labelledby="chat-title">
          <header className="chat-header">
            <div className="chat-heading">
              <div className="chat-title-row">
                <h2 id="chat-title">콤파 <span>COMPA</span></h2>
                <div className="chat-usage" ref={usageInfo}>
                  <span className="chat-usage-badge" role="status" aria-label={remaining == null ? 'AI 질문 횟수 확인 중' : `오늘 AI 질문 ${remaining}회 남음, 하루 최대 30회`}>
                    AI {remaining == null ? '…' : `${remaining}/30`}
                  </span>
                  <button className="chat-usage-button" type="button" ref={usageTrigger} aria-label="콤파 이용 안내"
                    aria-expanded={showUsageInfo} aria-controls="chat-usage-info" onClick={() => setShowUsageInfo(!showUsageInfo)}>
                    <Info size={theme.iconSize.sm} aria-hidden="true" />
                  </button>
                  {showUsageInfo && <div className="chat-usage-info" id="chat-usage-info">
                    <strong>오늘 남은 AI 질문 횟수예요</strong>
                    <p>직접 입력하는 AI 질문은 하루 30회까지이며, 한국 시간 자정에 초기화돼요. 질문은 최대 500자까지 입력할 수 있어요.</p>
                    <p>추천 질문과 파란색 용어 설명은 횟수 차감 없이 확인할 수 있어요.</p>
                    <p>이름·연락처 등 개인정보는 입력하지 마세요.</p>
                  </div>}
                </div>
              </div>
              <p>CreditComPass · 서비스와 차량 용어 안내</p>
            </div>
            <button type="button" aria-label="대화 초기화" disabled={pending || !loaded || messages.length === 0}
              onClick={resetConversation}>
              <RotateCcw size={theme.iconSize.sm} aria-hidden="true" />
            </button>
            <button type="button" onClick={close} aria-label="콤파 닫기"><X size={theme.iconSize.md} aria-hidden="true" /></button>
          </header>
          <div className="chat-messages" role="log" aria-label="콤파와의 대화" aria-live="polite" aria-relevant="additions text">
            <p className="chat-conversation-note">AI가 안내한 내용은 참고하시고,<br />중요한 정보는 한 번 더 확인해 주세요.</p>
            {messages.length === 0 && !pending ? (
              <div className="chat-welcome">
                <span className="chat-welcome-label">서비스 이용부터 자동차 용어까지</span>
                <h3>무엇이 궁금하신가요?<br />콤파에게 물어보세요.</h3>
                <p>이용 방법이 궁금할 때, 차종이 낯설 때<br />콤파가 알기 쉽게 안내해 드릴게요.<br />화면의 파란색 용어를 눌러도 좋아요.</p>
                <div className="chat-suggestions">
                  <div className="chat-categories" role="group" aria-label="질문 카테고리">
                    {categories.map(({ id, label, Icon }) => <button className="chat-category" type="button" key={id}
                      aria-pressed={categoryId === id} aria-controls="chat-category-questions" onClick={() => setCategoryId(id)}>
                      <Icon size={theme.iconSize.sm} aria-hidden="true" />{label}
                    </button>)}
                  </div>
                  <span className="chat-suggestions-label" id="chat-category-label">{category.label} · 이런 질문을 해보세요</span>
                  <div className="chat-category-questions" id="chat-category-questions" role="group" aria-labelledby="chat-category-label">
                  {category.questions.map(({ title, guideId }) => <button type="button" key={guideId} disabled={!loaded || pending} onClick={() => send(title, guideId)}>
                    <span className="chat-suggestion-icon"><category.Icon size={theme.iconSize.md} aria-hidden="true" /></span>
                    <span>{title}</span><ChevronRight size={theme.iconSize.sm} aria-hidden="true" />
                  </button>)}
                  </div>
                </div>
              </div>
            ) : null}
            {messages.map((message, index) => (
              <div className={`chat-bubble chat-${message.role}`} key={index}>
                <span className="chat-speaker">{message.role === 'user' ? '나' : <><Compass size={theme.iconSize.sm} aria-hidden="true" /> 콤파</>}</span>
                <p>{message.text}</p>
              </div>
            ))}
            {pending && <div className="chat-progress" role="status">
              <p>콤파가 안내를 준비하고 있어요… 잠시만 기다려 주세요.</p>
            </div>}
            {questionRequest && pending && <p className="chat-progress" role="status">현재 답변이 끝나면 ‘{questionRequest.label}’도 설명해 드릴게요.</p>}
            <div ref={bottom} />
          </div>
          {error && <p className="chat-error" role="alert">{error}</p>}
          {!loaded && <div className="chat-progress"><button type="button" disabled={pending} onClick={reloadHistory}>대화 기록 다시 불러오기</button></div>}
          <form className="chat-form" onSubmit={(event) => { event.preventDefault(); send(); }} aria-busy={pending}>
            <label className="chat-input-label" htmlFor="chat-question">질문 입력</label>
            <textarea id="chat-question" ref={input} value={draft} maxLength={500} rows={1}
              placeholder="이용 방법이나 궁금한 용어를 물어보세요" disabled={pending || !loaded || remaining === 0}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault(); send();
                }
              }} />
            <button type="submit" disabled={pending || !loaded || remaining === 0 || !draft.trim()} aria-label="질문 보내기">
              <Send size={theme.iconSize.md} aria-hidden="true" />
            </button>
          </form>
        </section>
      )}
      <button className="chat-trigger" ref={trigger} type="button" onClick={() => { returnFocus.current = trigger.current; setOpen(!open); }}
        aria-label={open ? '콤파 닫기' : 'AI 길잡이 콤파와 대화하기'} aria-expanded={open} aria-controls="chat-panel">
        {open ? <X size={theme.iconSize.lg} aria-hidden="true" /> : <><Compass size={theme.iconSize.lg} aria-hidden="true" /><span>콤파</span></>}
      </button>
    </div>
  );
}
