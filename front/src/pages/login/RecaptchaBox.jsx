// 보완 6: Google reCAPTCHA v2 "로봇이 아닙니다" 체크박스
// 로그인에 여러 번 실패해 서버가 CAPTCHA_REQUIRED 를 돌려줬을 때만 로그인 화면에 나타난다.
// 체크하면 구글이 만든 토큰을 onChange(token) 으로 알려 주고, 로그인 요청에 함께 보낸다 (서버가 구글에 진짜인지 확인).
import { useEffect, useRef, useState } from 'react';

// 사이트 키는 화면에 공개돼도 되는 키. 환경변수가 없으면 구글이 공개한 테스트 키(항상 통과)를 쓴다
const SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY ?? '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI';

let scriptPromise = null; // 구글 스크립트는 한 번만 불러온다

function loadRecaptcha() {
  if (window.grecaptcha?.render) return Promise.resolve(window.grecaptcha);
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      window.__onRecaptchaLoad = () => resolve(window.grecaptcha);
      const script = document.createElement('script');
      script.src = 'https://www.google.com/recaptcha/api.js?onload=__onRecaptchaLoad&render=explicit&hl=ko';
      script.async = true;
      script.onerror = () => {
        scriptPromise = null; // 다음에 다시 시도할 수 있게
        reject(new Error('reCAPTCHA 스크립트를 불러오지 못했습니다.'));
      };
      document.head.appendChild(script);
    });
  }
  return scriptPromise;
}

// onChange: 토큰을 받을 함수 (useState 의 set 함수처럼 바뀌지 않는 함수를 넘긴다)
// resetKey: 값이 바뀌면 체크를 풀고 토큰을 비운다 (토큰은 한 번만 쓸 수 있어서 로그인 실패 후 다시 체크해야 한다)
export default function RecaptchaBox({ onChange, resetKey }) {
  const boxRef = useRef(null);
  const widgetIdRef = useRef(null);
  const [loadError, setLoadError] = useState(false);

  // 처음 나타날 때 스크립트를 불러와 체크박스를 그린다
  useEffect(() => {
    let cancelled = false;
    loadRecaptcha()
      .then((grecaptcha) => {
        if (cancelled || !boxRef.current || widgetIdRef.current !== null) return;
        widgetIdRef.current = grecaptcha.render(boxRef.current, {
          sitekey: SITE_KEY,
          callback: (token) => onChange(token),
          'expired-callback': () => onChange(''), // 체크 후 2분이 지나면 토큰 만료
          'error-callback': () => onChange(''),
        });
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [onChange]);

  // 로그인이 다시 실패하면 체크를 풀어 새 토큰을 받게 한다
  useEffect(() => {
    if (resetKey === 0 || widgetIdRef.current === null) return;
    window.grecaptcha.reset(widgetIdRef.current);
    onChange('');
  }, [resetKey, onChange]);

  return (
    <div className="login-recaptcha">
      <p>로그인에 여러 번 실패했어요. 로봇이 아님을 확인해 주세요.</p>
      <div ref={boxRef} />
      {loadError && (
        <p className="login-error" role="alert">
          확인 도구를 불러오지 못했습니다. 인터넷 연결을 확인한 뒤 새로고침해 주세요.
        </p>
      )}
    </div>
  );
}
