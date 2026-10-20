// 보완 8: "Google 로 계속하기" 버튼 (Google Identity Services)
// 구글 창에서 계정을 고르면 구글이 ID 토큰(credential)을 주고, onCredential(idToken) 으로 알려 준다 → 서버가 구글에 확인
// Client ID 는 화면에 공개되는 값(VITE_GOOGLE_CLIENT_ID). 없으면 "설정 필요" 버튼만 보여 준다
import { useEffect, useRef, useState } from 'react';

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '';
// 보완 8 추가(10-20): Google Console 에는 http://localhost:5173 을 등록한다 → 127.0.0.1 로 열면 구글 버튼이 오류를 낸다
const WRONG_HOST = window.location.hostname === '127.0.0.1';
const HOST_HINT = 'localhost 주소(http://localhost:5173)로 접속해야 구글 로그인을 쓸 수 있습니다.';

let scriptPromise = null; // 구글 스크립트는 한 번만 불러온다

function loadGoogle() {
  if (window.google?.accounts?.id) return Promise.resolve(window.google);
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.onload = () => resolve(window.google);
      script.onerror = () => {
        scriptPromise = null;
        reject(new Error('구글 스크립트를 불러오지 못했습니다.'));
      };
      document.head.appendChild(script);
    });
  }
  return scriptPromise;
}

// onCredential: ID 토큰을 받을 함수 (useCallback 등으로 바뀌지 않는 함수를 넘긴다)
export default function GoogleLoginButton({ onCredential }) {
  const boxRef = useRef(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!CLIENT_ID) return undefined;
    let cancelled = false;
    loadGoogle()
      .then((google) => {
        if (cancelled || !boxRef.current) return;
        google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: (response) => onCredential(response.credential),
        });
        google.accounts.id.renderButton(boxRef.current, {
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          locale: 'ko',
          width: 320,
        });
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [onCredential]);

  if (!CLIENT_ID) {
    return (
      <div className="login-google">
        <button className="login-google-disabled" type="button" disabled>
          <span aria-hidden="true">G</span> Google 로 계속하기
        </button>
        <p className="login-google-hint">구글 로그인 설정이 필요합니다. (VITE_GOOGLE_CLIENT_ID)</p>
        {WRONG_HOST && <p className="login-google-hint">{HOST_HINT}</p>}
      </div>
    );
  }
  return (
    <div className="login-google">
      <div ref={boxRef} />
      {WRONG_HOST && <p className="login-google-hint">{HOST_HINT}</p>}
      {loadError && <p className="login-error">구글 로그인을 불러오지 못했습니다. 인터넷 연결을 확인해 주세요.</p>}
    </div>
  );
}
