import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { Compass, Car, ClipboardList, BookOpen, ChevronRight, X, Send, RotateCcw } from 'lucide-react';
import theme from '../../styles/theme';
import { sendChatMessage } from './chatApi';
import useChatStore from './useChatStore';
import './ChatWidget.css';

const categories = [
  { id: 'service', label: '서비스 이용', Icon: ClipboardList, questions: [
    { title: '서비스를 어떻게 이용하나요?', text: 'CreditComPass의 주요 기능과 처음 이용할 때의 순서를 알려주세요.' },
    { title: '취향 테스트 결과는 어떻게 저장하나요?', text: '취향 테스트 결과는 어떻게 저장하나요?' },
    { title: '차량을 비교하려면 어떻게 하나요?', text: '차량 비교 기능을 이용하는 방법을 알려주세요.' },
  ] },
  { id: 'body', label: '차종 도감', Icon: Car, questions: [
    { title: 'MPV는 어떤 차인가요?', text: 'MPV의 쉬운 뜻과 SUV와의 차이를 알려주세요.' },
    { title: '중형 SUV는 어떤 차인가요?', text: 'MIDSIZE_SUV(중형 SUV)의 쉬운 뜻과 다른 SUV 차급과의 차이를 알려주세요.' },
    { title: '세단과 SUV는 어떻게 다른가요?', text: '세단과 SUV의 차이를 쉽게 설명해 주세요.' },
  ] },
  { id: 'terms', label: '자동차 용어', Icon: BookOpen, questions: [
    { title: '하이브리드는 무엇인가요?', text: '하이브리드와 전기차의 차이를 쉽게 설명해 주세요.' },
    { title: '복합연비는 무슨 뜻인가요?', text: '복합연비와 km/L가 무슨 뜻인지 쉽게 알려주세요.' },
    { title: 'PHEV와 일반 하이브리드는 다른가요?', text: 'PHEV와 일반 하이브리드의 차이를 쉽게 설명해 주세요.' },
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
  const category = categories.find((item) => item.id === categoryId);
  const panel = useRef(null);
  const trigger = useRef(null);
  const input = useRef(null);
  const bottom = useRef(null);
  const activeRequest = useRef(null);
  const mounted = useRef(false);
  const returnFocus = useRef(null);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; activeRequest.current?.abort(); };
  }, []);

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

  async function send(text = draft) {
    const question = text.trim();
    if (!question || question.length > 2000 || activeRequest.current) return;
    const controller = new AbortController();
    activeRequest.current = controller;
    setPending(true);
    setError('');
    setDraft('');
    const history = messages.slice(-12).map(({ role, text: content }) => ({ role, text: content.slice(0, 6000) }));
    setMessages([...messages, { role: 'user', text: question }]);
    try {
      const result = await sendChatMessage(question, history, controller.signal);
      setMessages([...messages, { role: 'user', text: question },
        { role: 'model', text: result.answer }]);
    } catch (failure) {
      if (mounted.current) {
        setMessages(messages);
        setDraft(question);
        setError(controller.signal.aborted ? '답변 요청을 취소했습니다. 질문을 다시 보낼 수 있습니다.'
          : failure.response?.data?.error?.message || '답변을 불러오지 못했습니다. 다시 보내 주세요.');
      }
    } finally {
      activeRequest.current = null;
      if (mounted.current) setPending(false);
    }
  }

  const sendExplanation = useEffectEvent((question) => { void send(question); });
  useEffect(() => {
    if (!questionRequest || pending) return;
    let cancelled = false;
    // A term click is an external request; defer until this committed view is ready.
    queueMicrotask(() => {
      if (cancelled || activeRequest.current) return;
      returnFocus.current = questionRequest.returnFocus;
      consumeQuestion(questionRequest.id);
      sendExplanation(questionRequest.text);
    });
    return () => { cancelled = true; };
  }, [questionRequest, pending, consumeQuestion]);

  function close() {
    setOpen(false);
    (returnFocus.current?.isConnected ? returnFocus.current : trigger.current)?.focus();
  }

  return (
    <div className="chat-widget">
      {open && (
        <section className="chat-panel" id="chat-panel" ref={panel} role="region" aria-labelledby="chat-title">
          <header className="chat-header">
            <div className="chat-heading"><h2 id="chat-title">콤파 <span>COMPA</span></h2><p>CreditComPass · 서비스와 차량 용어 안내</p></div>
            <button type="button" aria-label="대화 초기화" disabled={pending || messages.length === 0}
              onClick={() => { setMessages([]); setError(''); setDraft(''); input.current?.focus(); }}>
              <RotateCcw size={theme.iconSize.sm} aria-hidden="true" />
            </button>
            <button type="button" onClick={close} aria-label="콤파 닫기"><X size={theme.iconSize.md} aria-hidden="true" /></button>
          </header>
          <div className="chat-messages" role="log" aria-label="콤파와의 대화" aria-live="polite" aria-relevant="additions text">
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
                  {category.questions.map(({ title, text }) => <button type="button" key={text} onClick={() => send(text)}>
                    <span className="chat-suggestion-icon"><category.Icon size={theme.iconSize.md} aria-hidden="true" /></span>
                    <span>{title}</span><ChevronRight size={theme.iconSize.sm} aria-hidden="true" />
                  </button>)}
                  </div>
                </div>
              </div>
            ) : <p className="chat-conversation-note">서비스 이용과 자동차 용어, 콤파에게 물어보세요.</p>}
            {messages.map((message, index) => (
              <div className={`chat-bubble chat-${message.role}`} key={index}>
                <span className="chat-speaker">{message.role === 'user' ? '나' : <><Compass size={theme.iconSize.sm} aria-hidden="true" /> 콤파</>}</span>
                <p>{message.text}</p>
              </div>
            ))}
            {pending && <div className="chat-progress" role="status">
              <p>콤파가 안내를 준비하고 있어요… 최대 60초 정도 걸릴 수 있습니다.</p>
              <button type="button" onClick={() => activeRequest.current?.abort()}>요청 취소</button>
            </div>}
            {questionRequest && pending && <p className="chat-progress" role="status">현재 답변이 끝나면 ‘{questionRequest.label}’도 설명해 드릴게요.</p>}
            <div ref={bottom} />
          </div>
          {error && <p className="chat-error" role="alert">{error}</p>}
          <form className="chat-form" onSubmit={(event) => { event.preventDefault(); send(); }} aria-busy={pending}>
            <label className="chat-input-label" htmlFor="chat-question">질문 입력</label>
            <textarea id="chat-question" ref={input} value={draft} maxLength={2000} rows={1}
              placeholder="이용 방법이나 궁금한 용어를 물어보세요" disabled={pending}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault(); send();
                }
              }} />
            <button type="submit" disabled={pending || !draft.trim()} aria-label="질문 보내기">
              <Send size={theme.iconSize.md} aria-hidden="true" />
            </button>
          </form>
          <p className="chat-footer">콤파는 AI 길잡이예요. 중요한 내용은 한 번 더 확인해 주세요.</p>
        </section>
      )}
      <button className="chat-trigger" ref={trigger} type="button" onClick={() => { returnFocus.current = trigger.current; setOpen(!open); }}
        aria-label={open ? '콤파 닫기' : 'AI 길잡이 콤파와 대화하기'} aria-expanded={open} aria-controls="chat-panel">
        {open ? <X size={theme.iconSize.lg} aria-hidden="true" /> : <><Compass size={theme.iconSize.lg} aria-hidden="true" /><span>콤파</span></>}
      </button>
    </div>
  );
}
