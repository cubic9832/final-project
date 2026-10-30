import react, { reactCompilerPreset } from '@vitejs/plugin-react';
import babel from '@rolldown/plugin-babel';
import { defineConfig } from 'vite';

// /api 로 시작하는 요청을 Spring Boot 로 전달한다 (개발 서버 전용)
const API_TARGET = 'http://localhost:8080';

export default defineConfig({
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  server: {
    // 같은 네트워크의 다른 PC에서도 개발 서버에 접속한다. 기본값은 localhost뿐이라 끈다.
    host: true,
    port: 5173,
    proxy: {
      '/api/v2': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
      '/api/v1/recommendations': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
      // 8단계: 1:1 상담 채팅 WebSocket. ws: true 가 있어야 WebSocket 연결을 넘겨준다 (강의 샘플 step4 와 같음)
      '/ws': {
        target: API_TARGET,
        ws: true,
      },
    },
  },
});
