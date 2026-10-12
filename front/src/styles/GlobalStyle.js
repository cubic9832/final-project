import { createGlobalStyle } from 'styled-components';

const GlobalStyle = createGlobalStyle`
  *, *::before, *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Noto Sans KR', sans-serif;
    color: ${({ theme }) => theme.colors.text};
    background: ${({ theme }) => theme.colors.background};
    line-height: 1.5;
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
`;

export default GlobalStyle;
