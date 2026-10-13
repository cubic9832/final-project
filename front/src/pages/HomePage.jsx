import { Link } from 'react-router-dom';
import { ArrowRight, ArrowUpRight } from 'lucide-react';
import theme from '../styles/theme';
import './HomePage.css';

const steps = [
  ['01', '재무 진단', '소득, 자산, 부채, 신용정보를 입력하면 구매 여력을 분석합니다.'],
  ['02', '맞춤 차량 찾기', '예산과 선호에 맞는 차량을 추천하고 적합한 이유를 보여드립니다.'],
  ['03', '구매 조건 설계', '현금과 할부 비율을 비교해 내 상황에 맞는 구매 방법을 확인합니다.'],
];

const benefits = [
  ['적정 예산', '조건에 맞는 차량만 빠르게', '차량 가격, 금융 비용까지 고려한 추천을 제공합니다.'],
  ['계약 비교', '가장 부담 없는 할부 비교', '금리, 기간, 월 납입금을 한눈에 비교해 보세요.'],
  ['후속 관리', '추천 결과 그 이후까지 투명하게', '어떤 정보와 기준이 반영됐는지 쉽게 확인할 수 있습니다.'],
];

export default function HomePage() {
  return (
    <div className="auto-home">
      <section className="hero" id="intro">
        <div className="landing-container hero-grid">
          <div className="hero-copy">
            <span className="eyebrow mint">내 재무 상황에 가장 적합한 자동차</span>
            <h1>
              살 수 있는 차가 아니라,
              <br />
              부담 없이 탈 수 있는 차를 찾으세요.
            </h1>
            <p>
              소득·자산·부채·신용정보를 분석해 내 재무상태에 맞는 차량 예산을 계산하고, 실제 구매 가능한 차량과 조건을 한 번에 비교합니다.
            </p>
            <div className="button-row">
              <a className="button primary" href="#financial">
                재무 진단 알아보기 <ArrowUpRight size={theme.iconSize.sm} aria-hidden="true" />
              </a>
              <Link className="button secondary" to="/search">
                차량 찾기 <ArrowRight size={theme.iconSize.sm} aria-hidden="true" />
              </Link>
            </div>
            <small>내 재무를 이해하는 것부터, 간편하게</small>
          </div>

          <article className="fit-card" aria-label="차량 적합도 예시">
            <div className="card-heading">
              <span className="eyebrow blue">MY FIT</span>
              <h2>부담 적합도 미리보기</h2>
              <span className="example">예시</span>
            </div>
            <div className="fit-summary">
              <div className="score">
                <small>현재 적합도</small>
                <strong>
                  82<span>점</span>
                </strong>
                <small>/ 100</small>
              </div>
              <div className="budget">
                <small>추천 차량 예산</small>
                <strong>2,800만 원 이하</strong>
                <small>월 부담 기준의 안전 구간</small>
              </div>
            </div>
            <div className="meter-label">
              <strong>월 소득 대비 자동차 비용</strong>
              <span>권장 범위</span>
            </div>
            <div className="meter">
              <span />
            </div>
            <p className="fit-note">무리 없는 예산, 충분한 선택의 여유</p>
            <div className="tags">
              <span>안정</span>
              <span>소득 반영</span>
              <span>선호 반영</span>
            </div>
          </article>
        </div>
      </section>

      <div className="trust-strip landing-container">
        <div>
          <strong>재무상태 반영</strong>
          <p>소득·자산·부채를 함께 분석</p>
        </div>
        <div>
          <strong>차량비용 계산</strong>
          <p>구매부터 유지까지 현실적인 기준</p>
        </div>
        <div>
          <strong>비교·시뮬레이션</strong>
          <p>같은 차량도 조건에 따라 다르게</p>
        </div>
      </div>

      <section className="steps-section" id="how-it-works">
        <div className="landing-container">
          <h2>복잡한 자동차 구매를 3단계로 단순하게</h2>
          <p className="section-description">
            재무 진단부터 차량 추천, 구매 조건 비교까지 한 흐름으로 이어집니다.
          </p>
          <div className="step-grid">
            {steps.map(([n, title, text]) => (
              <article className="step-card" key={n}>
                <span className="step-number">{n}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="financial-section landing-container" id="financial">
        <article className="financial-card">
          <span className="eyebrow white">FINANCIAL CHECK</span>
          <h2>
            내 재무상태에서
            <br />
            차량에 얼마까지 써도 될까?
          </h2>
          <p>월 소득뿐 아니라 자산과 부채, 신용정보까지 함께 반영해 감당 가능한 범위를 보여드립니다.</p>
          <div className="finance-metrics">
            <div>
              <small>월 가용 예산</small>
              <strong>75만 원</strong>
            </div>
            <div>
              <small>추천 월 납입금</small>
              <strong>58만 원</strong>
            </div>
            <div>
              <small>부담 수준</small>
              <strong>안정</strong>
            </div>
          </div>
          <small className="sample-note">이해를 돕기 위한 예시입니다.</small>
        </article>
        <div className="benefit-list">
          {benefits.map(([tag, title, text]) => (
            <article className="benefit-card" key={tag}>
              <div>
                <span className="eyebrow mint">{tag}</span>
                <h3>{title}</h3>
              </div>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="explain-section" id="analysis">
        <div className="landing-container explain-grid">
          <div>
            <span className="eyebrow blue">EXPLAINABLE MODEL</span>
            <h2>
              추천을 믿을 수 있도록
              <br />
              분석 과정도 보여드립니다.
            </h2>
            <p>
              신용·재무 정보와 선호도, 차량 가격, 유지 비용을 어떻게 반영했는지 확인하고 나에게 맞는 선택을 해보세요.
            </p>
            <a className="button secondary" href="#analysis-factors">
              분석 기준 알아보기 <ArrowRight size={theme.iconSize.sm} aria-hidden="true" />
            </a>
          </div>
          <article className="factor-card" id="analysis-factors">
            <h3>분석 설명에 포함될 주요 요인</h3>
            {[
              ['월 가용 소득', '중요'],
              ['총 부채 부담 수준', '보통'],
              ['선호 차량 유형', '반영'],
              ['차량 유지 비용', '보통'],
            ].map(([name, status]) => (
              <div className="factor" key={name}>
                <span>{name}</span>
                <span className={`eyebrow ${status === '반영' ? 'mint' : 'blue'}`}>{status}</span>
              </div>
            ))}
          </article>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-container">
          <h2>내 재무에 맞는 자동차 예산부터 확인해 보세요.</h2>
          <p>무리 없는 선택으로 향하는 가장 현실적인 시작입니다.</p>
          <a className="footer-link" href="#financial">
            내 자동차 예산 확인하기 <ArrowUpRight size={theme.iconSize.sm} aria-hidden="true" />
          </a>
          <div className="footer-bottom">
            <strong>CreditComPass Auto</strong>
            <p>재무 데이터로 더 나은 자동차 구매를 제안합니다.</p>
            <small>
              © {new Date().getFullYear()} CreditComPass Auto. · 본 화면의 수치는 예시이며 실제 분석 결과가 아닙니다.
            </small>
          </div>
        </div>
      </footer>
    </div>
  );
}
