import { createGlobalStyle } from 'styled-components';

const toKebab = (key) => key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);

// 일반 .css 파일에서도 테마 토큰을 쓸 수 있도록 CSS 변수로 내보낸다.
const cssVariables = (prefix, tokens) =>
  Object.entries(tokens)
    .map(([key, value]) => `--${prefix}-${toKebab(key)}: ${value};`)
    .join('\n');

const GlobalStyle = createGlobalStyle`
  :root {
    ${({ theme }) => cssVariables('color', theme.colors)}
    ${({ theme }) => cssVariables('font', theme.fontSize)}
    ${({ theme }) => cssVariables('radius', theme.radius)}
    ${({ theme }) => cssVariables('space', theme.spacing)}
    --layout-max-width: ${({ theme }) => theme.layout.maxWidth};
    --layout-gutter: ${({ theme }) => theme.layout.gutter};
    --layout-control-height: ${({ theme }) => theme.layout.controlHeight};
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.desktop}) {
    :root {
      --layout-gutter: ${({ theme }) => theme.layout.gutterTablet};
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.tablet}) {
    :root {
      --layout-gutter: ${({ theme }) => theme.layout.gutterMobile};
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.mobile}) {
    :root {
      ${({ theme }) => cssVariables('font', theme.fontSizeMobile)}
    }
  }

  *, *::before, *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html {
    scroll-behavior: smooth;
    scroll-padding-top: 96px;
  }

  body {
    font-family: 'Noto Sans KR', sans-serif;
    font-size: var(--font-body);
    color: var(--color-text);
    background: var(--color-background);
    line-height: 1.5;
  }

  h1, h2, h3, h4 {
    color: var(--color-primary);
    font-weight: 700;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  button, input, select, textarea {
    font: inherit;
  }

  button {
    cursor: pointer;
  }

  ul, ol {
    list-style: none;
  }

  section[id], article[id] {
    scroll-margin-top: 96px;
  }

  a:focus-visible,
  button:focus-visible,
  input:focus-visible,
  select:focus-visible {
    outline: 2px solid var(--color-blue);
    outline-offset: 2px;
  }

  @media (prefers-reduced-motion: reduce) {
    html {
      scroll-behavior: auto;
    }
  }
`;

export default GlobalStyle;
