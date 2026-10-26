import { useEffect, useRef } from 'react';

export default function TasteQuestion({ step, answers, question, questionCount, onSelect, onPrevious, onNext }) {
  const heading = useRef(null);
  const selected = answers[step];
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [step]);

  return (
    <form className="taste-question taste-card" onSubmit={(event) => { event.preventDefault(); if (selected !== null) onNext(); }}>
      <div className="taste-progress-label"><span>QUESTION {String(step + 1).padStart(2, '0')}</span><span>{step + 1} / {questionCount}</span></div>
      <progress className="taste-progress" value={step + 1} max={questionCount} aria-label="첫 차 취향 테스트 진행률" />
      <h1 ref={heading} tabIndex={-1} id="taste-question-title">{question.title}</h1>
      <fieldset className="taste-options" aria-labelledby="taste-question-title">
        <legend className="taste-sr-only">답변 하나 선택</legend>
        {question.options.map((option, index) => (
          <label className="taste-option" key={`${question.id}-${index}`}>
            <input type="radio" name={`taste-question-${step}`} value={index} checked={selected === index} onChange={() => onSelect(index)} />
            <span className="taste-option-content"><span className="taste-option-letter" aria-hidden="true">{'ABCD'[index]}</span><span>{option.text}</span></span>
          </label>
        ))}
      </fieldset>
      <div className="taste-actions"><button className="taste-button taste-button-outline" type="button" onClick={onPrevious}>이전</button><button className="taste-button taste-button-cta" type="submit" disabled={selected === null}>{step === questionCount - 1 ? '내 첫 차 취향 확인하기' : '다음'}</button></div>
    </form>
  );
}
