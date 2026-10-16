// 이메일 알림 범위 선택지. value 는 서버에 보낼 값, label 은 화면 문구
// 이메일 알림 설정 팝업과 마이페이지 "계정 및 데이터" 목록이 함께 쓴다.
export const NOTIFICATION_OPTIONS = [
  { value: 'ALL', label: '모든 알림 수신', description: '구매계획, 분석 결과, 차량 추천 업데이트를 받습니다.' },
  { value: 'IMPORTANT', label: '중요 계획 알림만 수신', description: '저장한 구매계획의 목표일·진행 상황만 받습니다.' },
  { value: 'NONE', label: '받지 않음', description: '이메일 알림을 보내지 않습니다.' },
];
