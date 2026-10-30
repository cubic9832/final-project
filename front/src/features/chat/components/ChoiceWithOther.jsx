import { OTHER } from '../choice';

// 8단계: 자주 있는 것을 고르고, 없으면 [기타] → 직접 쓰기 (상담 제한 · 넘기기 · 경고 사유, 만족도 의견 · 신고 사유)

// options 의 마지막에 OTHER 를 넣어 두면 [기타] 를 골랐을 때 직접 쓰는 칸이 나온다
// required 가 false 면 "선택 안 함" 이 기본값 (만족도 의견처럼 안 써도 되는 것)
export default function ChoiceWithOther({
  label, options, choice, other, onChoice, onOther, required = true, otherLabel = '직접 쓰기', maxLength = 200,
}) {
  return (
    <>
      <label>
        {label}
        <select value={choice} onChange={(event) => onChoice(event.target.value)} required={required}>
          <option value="">{required ? '선택하세요' : '선택 안 함'}</option>
          {options.map((option) => <option key={option} value={option}>{option}</option>)}
        </select>
      </label>
      {choice === OTHER && (
        <label>
          {otherLabel}
          <input value={other} onChange={(event) => onOther(event.target.value)} maxLength={maxLength} required placeholder="내용을 직접 적어 주세요" />
        </label>
      )}
    </>
  );
}
