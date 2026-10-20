import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { changePassword, logout } from '../../features/auth/authApi';
import { getMe, updateNickName, withdraw } from '../../features/auth/memberApi';
import useAuthStore from '../../stores/useAuthStore';
import AccountManageModal from './AccountManageModal';
import PasswordChangeModal from './PasswordChangeModal';
import AuthToast from '../../features/auth/components/AuthToast';
import EmailNotificationModal from './EmailNotificationModal';
import { NOTIFICATION_OPTIONS } from './notificationOptions';
import ProfileEditModal from './ProfileEditModal';
import { showToast } from '../../stores/useToastStore';
import './MyPage.css';

// 서버의 role 값 → 화면에 보여 줄 이름
const ROLE_LABELS = { USER: '사용자', ADMIN: '관리자' };

// 프로필 카드: 닉네임 · 이메일 · 권한은 서버(GET /members/me)에서 받아 채운다.
// tag 는 아직 저장하는 곳이 없어 예시 값으로 둔다.
const initialProfile = {
  nickname: '',
  email: '',
  role: '',
  tag: '취업 2년 차',
};

// ── 예시 데이터 (Figma 2조 류상민 ACCOUNT 01 기준) ──
// 아래 활동 · 관심차량 · 분석 · 구매계획은 백엔드 연결 전이라 화면 확인용 값만 둔다. 실제 회원·금액 정보가 아니다.

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

export default function MyPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(initialProfile);
  const [meStatus, setMeStatus] = useState('loading'); // 내 정보 불러오기: 'loading' | 'done' | 'error'
  const [reloadKey, setReloadKey] = useState(0); // 값이 바뀌면 내 정보를 다시 불러온다 (다시 시도 버튼)
  const [isEditOpen, setIsEditOpen] = useState(false);
  const editButtonRef = useRef(null); // 팝업을 닫으면 이 버튼으로 포커스를 돌려준다
  // 계정 및 데이터 팝업: 'notification'(이메일 알림 설정) | 'password'(비밀번호 변경, 보완 2 추가) | 'account'(회원 탈퇴) | null
  const [settingsModal, setSettingsModal] = useState(null);
  const [notification, setNotification] = useState('IMPORTANT'); // 이메일 알림 범위 (예시 값)
  const [toast, setToast] = useState(''); // 저장 결과 알림 문구 (빈 문자열이면 숨김)

  // 화면에 들어오면(또는 다시 시도하면) 서버에서 내 정보를 불러와 프로필 카드에 넣는다
  useEffect(() => {
    let ignore = false; // 응답이 오기 전에 화면을 떠나면 결과를 버린다
    getMe()
      .then((me) => {
        if (ignore) return;
        setProfile((prev) => ({
          ...prev,
          nickname: me.nickName,
          email: me.email,
          role: ROLE_LABELS[me.role] ?? me.role,
          socialOnly: me.socialOnly, // 보완 8: 구글로만 가입 → 탈퇴 확인 방법이 다르다
        }));
        setMeStatus('done');
      })
      .catch(() => {
        // 토큰 만료(401)면 client 인터셉터가 로그인 정보를 지워 RequireAuth 가 /login 으로 보낸다.
        // 그 밖의 실패(서버 꺼짐 등)는 다시 시도 버튼을 보여 준다.
        if (!ignore) setMeStatus('error');
      });
    return () => {
      ignore = true;
    };
  }, [reloadKey]);

  function handleRetry() {
    setMeStatus('loading');
    setReloadKey((key) => key + 1);
  }

  const planPercent = Math.round((savedPlan.saved / savedPlan.goal) * 100);
  const notificationLabel = NOTIFICATION_OPTIONS.find((option) => option.value === notification).label;

  // 보완 3 추가: 팝업에서 저장한 닉네임을 서버에 저장하고, 프로필 카드와 헤더에 반영한다
  // 실패하면(닉네임 중복 등) 예외가 팝업으로 전달되어 팝업 안에 오류가 표시된다
  async function handleSaveProfile(nickname) {
    const me = await updateNickName(nickname);
    setProfile((prev) => ({ ...prev, nickname: me.nickName }));
    useAuthStore.getState().updateMember({ nickName: me.nickName });
    closeEdit();
    setToast('프로필을 저장했어요.');
  }

  function handleSaveNotification(value) {
    setNotification(value);
    setSettingsModal(null);
    setToast('이메일 알림 설정을 저장했어요.');
  }

  // 보완 2 추가: 비밀번호 변경 — 실패하면 예외가 팝업으로 전달되어 팝업 안에 오류가 표시된다
  async function handleChangePassword(passwords) {
    await changePassword(passwords);
    setSettingsModal(null);
    setToast('비밀번호를 변경했어요. 다른 기기의 로그인은 끊었어요.');
  }

  // 회원 탈퇴 (보완 4): 서버 탈퇴 → 메인으로 이동 → 로그아웃 처리 → 공용 알림
  // 실패하면(비밀번호 틀림 등) 예외가 그대로 팝업으로 전달되어 팝업 안에 오류가 표시된다
  async function handleWithdraw(confirmation) {
    await withdraw(confirmation); // { password } 또는 구글 가입자는 { confirmText: '탈퇴' } (보완 8)
    setSettingsModal(null);
    navigate('/'); // 먼저 이동 — 로그인 정보가 지워지면 마이페이지 보호(RequireAuth)가 로그인 화면으로 보내기 때문
    await logout(); // 브라우저의 refresh token 쿠키 삭제 + 화면 로그인 정보 지우기 (서버 토큰은 탈퇴 때 이미 삭제됨)
    showToast('회원 탈퇴가 완료되었습니다. 그동안 이용해 주셔서 감사합니다.');
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
            <span className="my-example-badge">일부 예시 데이터</span>
          </div>
          <p>저장한 분석 결과와 관심차량, 구매계획을 한곳에서 관리하세요.</p>
        </div>
        {meStatus === 'done' && <span className="my-role-badge">{profile.role}</span>}
      </header>

      <div className="my-overview">
        <section className="my-card my-profile" aria-labelledby="my-profile-name">
          {meStatus === 'loading' && (
            <p id="my-profile-name" className="my-profile-status" role="status">
              내 정보를 불러오는 중입니다…
            </p>
          )}
          {meStatus === 'error' && (
            <>
              <p id="my-profile-name" className="my-profile-status" role="alert">
                내 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.
              </p>
              <button className="my-outline-button" type="button" onClick={handleRetry}>
                다시 시도
              </button>
            </>
          )}
          {meStatus === 'done' && (
            <>
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
            </>
          )}
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
          <li>
            <span>이메일 알림 · {notificationLabel}</span>
            <button className="my-text-button" type="button" onClick={() => setSettingsModal('notification')}>
              설정
            </button>
          </li>
          {/* 보완 2 추가: 구글로만 가입한 계정은 비밀번호가 없어 숨긴다 */}
          {!profile.socialOnly && (
            <li>
              <span>비밀번호 변경</span>
              <button className="my-text-button" type="button" onClick={() => setSettingsModal('password')}>
                변경
              </button>
            </li>
          )}
          <li>
            <span>회원 탈퇴</span>
            <button className="my-text-button" type="button" onClick={() => setSettingsModal('account')}>
              탈퇴
            </button>
          </li>
        </ul>
      </section>

      {/* 팝업은 열 때마다 새로 만들어서 입력값이 이전 상태로 남지 않게 한다 */}
      {isEditOpen && (
        <ProfileEditModal
          nickname={profile.nickname}
          email={profile.email}
          onSave={handleSaveProfile}
          onClose={closeEdit}
        />
      )}
      {settingsModal === 'notification' && (
        <EmailNotificationModal
          currentValue={notification}
          onSave={handleSaveNotification}
          onClose={() => setSettingsModal(null)}
        />
      )}
      {settingsModal === 'password' && (
        <PasswordChangeModal email={profile.email} onChange={handleChangePassword} onClose={() => setSettingsModal(null)} />
      )}
      {settingsModal === 'account' && (
        <AccountManageModal socialOnly={profile.socialOnly} onWithdraw={handleWithdraw} onClose={() => setSettingsModal(null)} />
      )}
      {toast && <AuthToast message={toast} onClose={() => setToast('')} />}
    </div>
  );
}
