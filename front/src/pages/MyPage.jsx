import { useRef, useState } from 'react';
import ProfileEditModal from '../components/ProfileEditModal';
import './MyPage.css';

// ── 예시 데이터 (Figma 2조 류상민 ACCOUNT 01 기준) ──
// 백엔드 연결 전이라 화면 확인용 값만 둔다. 실제 회원·금액 정보가 아니다.
const exampleProfile = {
  nickname: '김첫차',
  email: 'firstcar@example.com',
  role: '사용자',
  tag: '취업 2년 차',
};

const metrics = [
  { label: '관심차량', value: '4대', note: '최근 추가 2일 전' },
  { label: '이전 분석', value: '3건', note: '최근 분석 2026.10.01' },
  { label: '저장 계획', value: '1개', note: '목표까지 6개월', highlight: true },
];

const favoriteVehicle = {
  fitScore: '재무 적합도 91%',
  name: '현대 아반떼 하이브리드',
  summary: '2,380만 원 · 신차/하이브리드',
  stats: [
    { label: '월 할부금', value: '37만 원' },
    { label: '월 유지비', value: '16만 원' },
    { label: '복합연비', value: '21.1km/L' },
  ],
  reason: '출퇴근 거리가 길어 연료비 절감 효과가 큰 차량입니다.',
};

const analysisHistory = [
  { id: 1, title: '취업 2년 차 기본 분석', detail: '2026.10.01 · 권장 예산 1,800~2,400만 원', risk: '보통' },
  { id: 2, title: '선수금 800만 원 조건', detail: '2026.09.14 · 권장 예산 2,000~2,600만 원', risk: '낮음' },
  { id: 3, title: '중고차 포함 조건', detail: '2026.08.27 · 추천 차량 9대', risk: '보통' },
];

const savedPlan = {
  title: '아반떼 하이브리드 · 2027년 3월',
  dDay: 'D-180',
  saved: 500,
  goal: 800,
  monthlySaving: '50만 원',
  shortage: '300만 원',
};

const accountSettings = [
  { label: '이메일 알림 · 중요 계획 알림만 수신', action: '설정' },
  { label: '내 데이터 다운로드 및 회원 탈퇴', action: '관리' },
];

export default function MyPage() {
  const [profile, setProfile] = useState(exampleProfile);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const editButtonRef = useRef(null); // 팝업을 닫으면 이 버튼으로 포커스를 돌려준다

  const planPercent = Math.round((savedPlan.saved / savedPlan.goal) * 100);

  // 팝업에서 저장한 닉네임을 화면에 반영한다 (서버 저장은 API 연결 단계에서)
  function handleSaveProfile(nickname) {
    setProfile((prev) => ({ ...prev, nickname }));
    closeEdit();
  }

  function closeEdit() {
    setIsEditOpen(false);
    editButtonRef.current?.focus();
  }

  return (
    <div className="my-page">
      <header className="my-heading">
        <div>
          <div className="my-title-row">
            <h1>마이페이지</h1>
            <span className="my-example-badge">예시 데이터</span>
          </div>
          <p>저장한 분석 결과와 관심차량, 구매계획을 한곳에서 관리하세요.</p>
        </div>
        <span className="my-role-badge">{profile.role}</span>
      </header>

      <div className="my-overview">
        <section className="my-card my-profile" aria-labelledby="my-profile-name">
          <div className="my-profile-row">
            <div className="my-avatar" aria-hidden="true">
              {profile.nickname.charAt(0)}
            </div>
            <div className="my-identity">
              <h2 id="my-profile-name">{profile.nickname}님</h2>
              <p>{profile.email}</p>
            </div>
          </div>
          <div className="my-profile-badges">
            <span className="my-role-badge my-badge-small">{profile.role}</span>
            <span className="my-tag-badge">{profile.tag}</span>
          </div>
          <button
            ref={editButtonRef}
            className="my-outline-button"
            type="button"
            onClick={() => setIsEditOpen(true)}
          >
            프로필 수정
          </button>
        </section>

        <section className="my-metrics" aria-label="내 활동 요약">
          {metrics.map((metric) => (
            <article
              className={metric.highlight ? 'my-metric my-metric-highlight' : 'my-metric'}
              key={metric.label}
            >
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.note}</small>
            </article>
          ))}
        </section>
      </div>

      <div className="my-saved">
        <section className="my-favorites" aria-labelledby="my-favorites-title">
          <div className="my-section-heading">
            <div>
              <h2 id="my-favorites-title">관심차량</h2>
              <p>저장한 차량의 가격과 월 비용을 빠르게 비교하세요.</p>
            </div>
            <button className="my-text-button" type="button">전체 보기</button>
          </div>

          <article className="my-card my-vehicle-card">
            <div className="my-vehicle-image" aria-hidden="true">
              <span />
            </div>
            <span className="my-fit-badge">{favoriteVehicle.fitScore}</span>
            <h3>{favoriteVehicle.name}</h3>
            <p className="my-vehicle-summary">{favoriteVehicle.summary}</p>
            <dl className="my-vehicle-stats">
              {favoriteVehicle.stats.map((stat) => (
                <div key={stat.label}>
                  <dt>{stat.label}</dt>
                  <dd>{stat.value}</dd>
                </div>
              ))}
            </dl>
            <div className="my-vehicle-reason">
              <strong>추천 이유</strong>
              <p>{favoriteVehicle.reason}</p>
            </div>
          </article>
        </section>

        <div className="my-history-plan">
          <section className="my-card my-history" aria-labelledby="my-history-title">
            <div className="my-section-heading">
              <div>
                <h2 id="my-history-title">이전 분석 결과</h2>
                <p>조건별 분석 기록을 다시 열어볼 수 있습니다.</p>
              </div>
              <button className="my-text-button" type="button">모두 보기</button>
            </div>

            <ul className="my-history-list">
              {analysisHistory.map((record) => (
                <li className="my-history-record" key={record.id}>
                  <span className="my-record-icon" aria-hidden="true">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
                      <path d="M3 3v14h14M7 13V9m4 4V6m4 7v-3" strokeLinecap="round" />
                    </svg>
                  </span>
                  <div className="my-record-copy">
                    <strong>{record.title}</strong>
                    <span>{record.detail}</span>
                  </div>
                  <span className={record.risk === '낮음' ? 'my-risk my-risk-low' : 'my-risk'}>
                    {record.risk}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="my-plan" aria-labelledby="my-plan-title">
            <div className="my-plan-heading">
              <div>
                <span>저장한 구매계획</span>
                <h2 id="my-plan-title">{savedPlan.title}</h2>
              </div>
              <span className="my-plan-dday">{savedPlan.dDay}</span>
            </div>

            <div className="my-plan-progress">
              <div className="my-plan-progress-labels">
                <span>선수금 준비</span>
                <strong>
                  {savedPlan.saved} / {savedPlan.goal}만 원
                </strong>
              </div>
              <div
                className="my-plan-track"
                role="progressbar"
                aria-label="선수금 준비율"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={planPercent}
              >
                <span style={{ width: `${planPercent}%` }} />
              </div>
            </div>

            <div className="my-plan-summary">
              <div>
                <span>월 저축</span>
                <strong>{savedPlan.monthlySaving}</strong>
              </div>
              <div>
                <span>부족 금액</span>
                <strong>{savedPlan.shortage}</strong>
              </div>
            </div>

            <button className="my-plan-button" type="button">구매계획 이어보기</button>
          </section>
        </div>
      </div>

      <section className="my-card my-settings" aria-labelledby="my-settings-title">
        <div className="my-section-heading">
          <div>
            <h2 id="my-settings-title">계정 및 데이터</h2>
            <p>개인정보와 저장 데이터를 관리합니다.</p>
          </div>
        </div>
        <ul>
          {accountSettings.map((setting) => (
            <li key={setting.label}>
              <span>{setting.label}</span>
              <button className="my-text-button" type="button">{setting.action}</button>
            </li>
          ))}
        </ul>
      </section>

      {/* 열 때마다 새로 만들어서 입력값이 이전 상태로 남지 않게 한다 */}
      {isEditOpen && (
        <ProfileEditModal
          nickname={profile.nickname}
          email={profile.email}
          onSave={handleSaveProfile}
          onClose={closeEdit}
        />
      )}
    </div>
  );
}
