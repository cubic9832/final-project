// 7단계: 운영 로그 표시 도우미 (운영 로그 탭 · 운영 현황 "최근 운영 이력" 이 같이 쓴다)
import { ROLE_LABELS } from '../../features/auth/roles';

export const ACTION_LABELS = { ROLE_CHANGE: '권한 변경' };

// "2026-10-26T17:30:12" → "2026.10.26 17:30"
export const formatLogTime = (value) => `${value.slice(0, 10).replaceAll('-', '.')} ${value.slice(11, 16)}`;

// 이름이 없으면(탈퇴) 번호와 함께 "탈퇴한 회원"
export const personName = (nickName, id) => nickName ?? (id ? `탈퇴한 회원 #${id}` : '탈퇴한 회원');

// "USER → ADMIN" → "일반 회원 → 관리자" (권한 변경일 때)
export const describeLog = (log) =>
  log.action === 'ROLE_CHANGE'
    ? log.detail.split(' → ').map((role) => ROLE_LABELS[role] ?? role).join(' → ')
    : log.detail;
