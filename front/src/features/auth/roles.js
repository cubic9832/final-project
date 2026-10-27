// 7단계: 회원 권한 (users.role). 총관리자(SUPER_ADMIN)는 DB 에서만 정하고, 관리자 권한을 주고 뺄 수 있다
export const ROLE_LABELS = { USER: '일반 회원', ADMIN: '관리자', SUPER_ADMIN: '총관리자' };

// 관리자 화면에 들어갈 수 있는 권한인지 (관리자 · 총관리자)
export const isAdminRole = (role) => role === 'ADMIN' || role === 'SUPER_ADMIN';
