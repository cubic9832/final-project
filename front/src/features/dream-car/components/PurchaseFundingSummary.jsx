import { CalendarDays } from 'lucide-react';
import theme from '../../../styles/theme';
import './PurchaseFundingSummary.css';

const money = value => `${Math.round(value).toLocaleString('ko-KR')}만 원`;
export default function PurchaseFundingSummary({ result, inputs, baseDate }) {
  let arrival = '저축액을 입력해 주세요';
  if (result.months !== null) {
    const date = new Date(baseDate);
    date.setDate(1);
    date.setMonth(date.getMonth() + result.months);
    arrival = result.months === 0 ? '지금 목표를 달성했어요' : result.months > 1200 ? '100년 이상 · 저축액 조정 필요' : `${date.getFullYear()}년 ${date.getMonth() + 1}월 예상`;
  }
  return <section className="purchase-funding-summary"><span className="purchase-funding-eyebrow"><CalendarDays size={theme.iconSize.sm} aria-hidden />MY DREAM TIMELINE</span><p className="purchase-funding-label">드림카를 위한 준비 자금</p><strong className="purchase-funding-amount">{money(result.target)}</strong><p>차량 구매비 + {inputs.reserveMonths}개월 유지비 예비자금</p><div className="purchase-funding-progress-label"><span>목표 달성률</span><strong>{Math.floor(result.progress)}%</strong></div><progress value={result.progress} max="100" aria-label="구매 자금 달성률" /><div className="purchase-funding-metrics"><div><small>앞으로 모을 돈</small><strong>{money(result.remaining)}</strong></div><div><small>현재 저축 속도로</small><strong>{result.months === null ? '기간 산출 불가' : `${result.months}개월`}</strong></div></div><div className="purchase-funding-arrival">{arrival}</div></section>;
}
