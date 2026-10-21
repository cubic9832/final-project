import axios from 'axios';
import useAuthStore from '../../stores/useAuthStore.js';

// 진행 중인 재발급 요청. 여러 곳에서 동시에 불려도 서버에는 한 번만 보낸다.
// refresh token 은 쓸 때마다 새것으로 바뀌므로(rotation), 두 번 보내면 두 번째는 이미 바뀐 토큰이라 실패한다.
let refreshing = null;

// refresh token 쿠키로 새 access token 을 받아 스토어에 넣고, 새 access token 을 돌려준다
export const refreshAccessToken = () => {
  if (!refreshing) {
    // client 가 아니라 axios 를 직접 쓴다 → client 의 응답 인터셉터를 다시 타서 무한 반복하지 않게
    // 보완 1 추가(10-20): 실패하면 0.5초 뒤 한 번만 다시 시도한다
    // 다른 탭이 같은 순간에 재발급해서 쿠키가 막 새것으로 바뀐 경우, 다시 보내면 새 쿠키로 성공한다
    // 10-22: 서버가 응답하지 않아도 "확인 중"에서 멈추지 않게 5초 시간 제한 (넘으면 로그아웃 상태로 화면을 보여 준다)
    const post = () => axios.post('/api/v1/auth/refresh', null, { timeout: 5000 }); // refresh token 쿠키는 브라우저가 자동으로 실어 보낸다
    refreshing = post()
      .catch(() => new Promise((resolve) => setTimeout(resolve, 500)).then(post))
      .then((res) => {
        useAuthStore.getState().setAuth(res.data.data);
        return res.data.data.accessToken;
      })
      .catch((error) => {
        useAuthStore.getState().clearAuth(); // 재발급 실패 = 로그아웃 상태
        throw error;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
};
