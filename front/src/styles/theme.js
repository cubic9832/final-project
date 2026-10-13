// 값의 기준은 docs/ui.md다. GlobalStyle이 CSS 변수(--color-*, --font-* 등)로 내보낸다.
const theme = {
  colors: {
    primary: '#203960',
    primaryHover: '#2d4d7c',
    mint: '#54b19d',
    mintHover: '#6bbfac',
    mintStrong: '#2f8371', // 14px 이하 글자용
    mintTint: '#e8f5f1',
    blue: '#3f8ae2',
    blueStrong: '#2b6fc2', // 14px 이하 글자용
    blueTint: '#ecf3fc',
    text: '#1f2937',
    textSub: '#475569',
    muted: '#64748b',
    placeholder: '#94a3b8',
    textOnPrimary: '#c3d0e2',
    tintOnPrimary: '#ffffff14',
    background: '#f7f8fb',
    surface: '#ffffff',
    border: '#e2e8f0',
    borderInput: '#cbd5e1',
    danger: '#dc2626',
  },
  fontSize: {
    display: 'clamp(28px, 3.1vw, 44px)',
    pageTitle: '28px',
    sectionTitle: '24px',
    cardTitle: '20px',
    subtitle: '16px',
    body: '14px',
    caption: '12px',
    figureLg: '32px',
    figureMd: '20px',
  },
  // 480px 이하에서 줄어드는 제목 크기
  fontSizeMobile: {
    pageTitle: '24px',
    sectionTitle: '20px',
  },
  radius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    pill: '24px',
  },
  spacing: {
    4: '4px',
    8: '8px',
    12: '12px',
    16: '16px',
    24: '24px',
    32: '32px',
    48: '48px',
    64: '64px',
  },
  breakpoints: {
    desktop: '1024px',
    tablet: '768px',
    mobile: '480px',
  },
  layout: {
    maxWidth: '1280px',
    gutter: '32px',
    gutterTablet: '24px',
    gutterMobile: '16px',
    controlHeight: '40px',
  },
};

export default theme;
