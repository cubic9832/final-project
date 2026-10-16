// 첫 차 구매자를 위한 규칙 기반 취향 탐색. 운전 경험이나 재무정보는 요구하지 않는다.
const option = (text, weights) => ({ text, weights });
const question = (id, title, options) => ({ id, title, options });
export const TASTE_QUESTION_COUNT = 8;
export const TASTE_VERSION = 2;

export const firstQuestion = question('first-car', '첫 차가 생기면 가장 먼저 해보고 싶은 일은?', [
  option('가까운 카페나 맛집을 자유롭게 찾아가기', { city: 2 }),
  option('출퇴근길을 나만의 편안한 시간으로 만들기', { comfort: 2 }),
  option('짐을 싣고 근교 여행이나 캠핑 떠나기', { adventure: 2 }),
  option('가족이나 친구를 태우고 함께 나들이하기', { together: 2 }),
]);

export const purposeQuestions = [
  question('daily', '처음 가는 동네의 카페를 찾아갈 때, 어떤 차면 더 마음이 놓일까요?', [
    option('좁은 골목과 주차장에서도 부담 없는 작은 차', { city: 2 }),
    option('길을 잘못 들어도 차분하게 이동할 수 있는 편안한 차', { comfort: 2 }),
    option('구경하다 산 물건과 짐도 넉넉히 담을 수 있는 차', { adventure: 2 }),
    option('카페 앞에 세워두면 내 취향이 느껴지는 차', { explorer: 2 }),
  ]),
  question('commute', '첫 차로 매일 출퇴근한다면, 가장 바라는 점은?', [
    option('회사나 집의 좁은 주차장에 넣기 편했으면 좋겠다', { city: 2 }),
    option('퇴근 후 지친 몸을 편하게 맡길 수 있으면 좋겠다', { comfort: 2 }),
    option('퇴근 후 운동 가방이나 취미용품도 싣고 다니고 싶다', { adventure: 2 }),
    option('가족이나 동료와 함께 이동할 때도 여유로우면 좋겠다', { together: 2 }),
  ]),
  question('travel', '첫 차와 주말 여행을 떠날 때, 어떤 모습이 더 끌리나요?', [
    option('작은 가방 하나로 가볍게 근교를 다녀오기', { city: 2 }),
    option('편안한 실내에서 쉬엄쉬엄 먼 곳까지 이동하기', { comfort: 2 }),
    option('캠핑 장비나 취미용품을 싣고 새로운 곳 찾아가기', { adventure: 2 }),
    option('가족이나 친구들과 함께 추억 만들기', { together: 2 }),
  ]),
  question('company', '함께 나들이할 때, 첫 차에서 가장 챙기고 싶은 것은?', [
    option('약속 장소와 식당 주변에서 주차하기 쉬운 크기', { city: 2 }),
    option('이동하는 동안 편하게 대화할 수 있는 실내', { comfort: 2 }),
    option('여러 사람의 여행 가방도 담을 수 있는 짐 공간', { adventure: 2 }),
    option('동승자가 편하게 타고 앉을 수 있는 좌석', { together: 2 }),
  ]),
];

export const detailQuestions = {
  city: question('small-space', '다루기 편한 첫 차를 고른다면, 공간은 어느 정도면 좋을까요?', [
    option('평소 혼자 타고 작은 가방 정도만 넣으면 충분하다', { city: 2 }),
    option('혼자 또는 둘이 편하게 앉을 수 있으면 좋겠다', { comfort: 2 }),
    option('크기가 조금 커져도 여행 짐은 넉넉히 담고 싶다', { adventure: 2 }),
    option('가끔 태울 가족이나 친구의 뒷좌석도 챙기고 싶다', { together: 2 }),
  ]),
  comfort: question('comfortable-space', '첫 차 안에서 편안한 시간을 보낸다면, 무엇이 가장 중요할까요?', [
    option('필요한 기능을 쉽게 찾을 수 있는 간단한 조작부', { city: 2 }),
    option('혼자서도 아늑하게 쉴 수 있는 좌석과 분위기', { comfort: 2 }),
    option('여행 중 쉬거나 짐을 정리하기 좋은 여유 공간', { adventure: 2 }),
    option('나뿐 아니라 함께 타는 사람도 편안한 좌석', { together: 2 }),
  ]),
  adventure: question('luggage-space', '첫 차에 여행 짐을 싣는다면, 어떤 짐이 가장 자주 실릴까요?', [
    option('작은 배낭이나 장보기 가방 정도', { city: 2 }),
    option('가벼운 여행 가방과 편하게 쉴 담요', { comfort: 2 }),
    option('부피가 큰 캠핑 장비나 야외 취미용품', { adventure: 2 }),
    option('함께 타는 사람들의 가방이나 유아용품', { together: 2 }),
  ]),
  together: question('passenger-space', '첫 차의 동승자 공간은 누구를 떠올리며 고르고 싶나요?', [
    option('주로 혼자 타고, 가끔 친구 한 명이면 충분하다', { city: 2 }),
    option('연인이나 친구와 둘이 편하게 이동하고 싶다', { comfort: 2 }),
    option('사람도 태우고 여행 짐도 넉넉히 싣고 싶다', { adventure: 2 }),
    option('부모님이나 아이 등 가족의 승하차와 좌석을 챙기고 싶다', { together: 2 }),
  ]),
  explorer: question('personal-space', '내 취향이 담긴 첫 차, 실용성도 하나 챙긴다면?', [
    option('좁은 곳에서도 다루기 편한 크기', { city: 2 }),
    option('매일 머물러도 편안한 운전석', { comfort: 2 }),
    option('해보고 싶은 활동을 담을 수 있는 짐 공간', { adventure: 2 }),
    option('함께 타는 사람을 위한 여유로운 좌석', { together: 2 }),
  ]),
};

export const concernQuestion = question('concern', '처음 내 차를 운전한다고 상상하면, 가장 신경 쓰이는 것은?', [
  option('좁은 골목이나 주차장에서 차를 다루는 일', { city: 2 }),
  option('복잡한 버튼이나 기능에 익숙해지는 일', { city: 1, comfort: 1 }),
  option('오래 이동할 때 피곤하지 않을지', { comfort: 2 }),
  option('동승자가 편하게 타고 내릴 수 있을지', { together: 2 }),
]);

export const supportQuestions = [
  question('parking-support', '첫 차로 주차를 연습한다면, 무엇이 가장 든든할까요?', [
    option('차 폭과 길이를 가늠하기 쉬운 작은 차체', { city: 2 }),
    option('주변 장애물과 뒤쪽을 살피는 화면·알림', { city: 1, explorer: 1 }),
    option('몸을 편하게 움직이며 주변을 볼 수 있는 운전석', { comfort: 2 }),
    option('동승자도 여유 있게 타고 내릴 수 있는 문과 공간', { together: 2 }),
  ]),
  question('simple-controls', '처음 차의 기능을 익힐 때, 어떤 방식이 더 편할 것 같나요?', [
    option('자주 쓰는 기능이 눈에 보이는 버튼으로 있는 방식', { city: 2 }),
    option('기능은 많지 않아도 필요한 것을 쉽게 찾는 방식', { comfort: 2 }),
    option('익숙한 휴대폰과 연결해 화면에서 사용하는 방식', { explorer: 2 }),
    option('동승자도 좌석과 온도를 쉽게 조절할 수 있는 방식', { together: 2 }),
  ]),
  question('long-trip', '첫 장거리 나들이에서 가장 기대되는 편의는?', [
    option('쉬어갈 장소에서 주차하기 편한 크기', { city: 2 }),
    option('오래 앉아도 편안한 좌석과 조용한 실내', { comfort: 2 }),
    option('짐과 간식을 꺼내기 편한 수납공간', { adventure: 2 }),
    option('뒷좌석에서도 편하게 쉴 수 있는 여유', { together: 2 }),
  ]),
  question('passenger-support', '함께 탈 사람을 위해 하나를 더 챙긴다면?', [
    option('도착한 곳에서 쉽게 주차할 수 있는 크기', { city: 2 }),
    option('실내에서 편하게 대화할 수 있는 조용한 분위기', { comfort: 2 }),
    option('사람들의 짐을 한 번에 실을 수 있는 트렁크', { adventure: 2 }),
    option('타고 내리기 편하고 앉을 공간이 넉넉한 좌석', { together: 2 }),
  ]),
];

export const exteriorQuestion = question('exterior', '주차장에 서 있는 내 첫 차, 어떤 모습이면 기분이 좋을까요?', [
  option('작고 단정해서 친근한 모습', { city: 2 }),
  option('유행을 크게 타지 않는 깔끔한 모습', { comfort: 2 }),
  option('야외 풍경과 잘 어울리는 활동적인 모습', { adventure: 2 }),
  option('색상이나 디자인에서 개성이 느껴지는 모습', { explorer: 2 }),
]);
export const interiorQuestion = question('interior', '첫 차의 문을 열었을 때, 어떤 실내에서 지내고 싶나요?', [
  option('필요한 것만 깔끔하게 정리된 단순한 공간', { city: 2 }),
  option('따뜻한 색감과 편안한 소재가 있는 아늑한 공간', { comfort: 2 }),
  option('가족이나 친구와 함께 앉아도 여유로운 공간', { together: 2 }),
  option('화면과 조명에서 내 취향이 느껴지는 공간', { explorer: 2 }),
]);

export const confirmationQuestions = {
  city: question('confirm-city', '작고 다루기 편한 차에 마음이 가는 편이에요. 다른 매력과 비교하면 무엇을 우선할까요?', [
    option('짐 공간이 조금 작아도 주차하기 편한 크기', { city: 3 }),
    option('크기가 조금 커져도 매일 편안한 실내', { comfort: 3 }),
    option('주차 연습이 더 필요해도 여행 짐을 담는 공간', { adventure: 3 }),
    option('크기보다는 볼 때마다 기분 좋은 디자인', { explorer: 3 }),
  ]),
  comfort: question('confirm-comfort', '편안한 일상을 기대하고 있어요. 첫 차에서 마지막으로 우선할 것은?', [
    option('실내가 조금 작아도 다루기 부담 없는 크기', { city: 3 }),
    option('다른 특징보다 매일 편안하게 지낼 실내', { comfort: 3 }),
    option('편안함만큼 중요한 여행·취미용 짐 공간', { adventure: 3 }),
    option('나뿐 아니라 함께 타는 사람의 편안함', { together: 3 }),
  ]),
  adventure: question('confirm-adventure', '여행과 활동을 담을 공간에 관심이 있어요. 첫 차에서 더 우선할 것은?', [
    option('큰 짐은 줄이더라도 평소 주차가 편한 크기', { city: 3 }),
    option('짐 공간보다는 매일 편하게 앉을 수 있는 실내', { comfort: 3 }),
    option('크기가 조금 커져도 여행 장비를 담는 공간', { adventure: 3 }),
    option('장비보다는 함께 탈 사람의 좌석 공간', { together: 3 }),
  ]),
  together: question('confirm-together', '함께 타는 사람을 많이 떠올렸어요. 내 첫 차를 고를 때 마지막 기준은?', [
    option('동승자는 가끔 태우니 혼자 다루기 편한 크기', { city: 3 }),
    option('큰 차보다는 혼자 또는 둘이 편하게 탈 실내', { comfort: 3 }),
    option('좌석만큼 여행 가방과 취미 장비를 담는 공간', { adventure: 3 }),
    option('크기가 조금 커져도 모두가 편하게 앉는 좌석', { together: 3 }),
  ]),
  explorer: question('confirm-explorer', '나만의 디자인과 분위기에 끌리고 있어요. 실용성과 비교하면 무엇을 고를까요?', [
    option('개성보다 처음 다루기 부담 없는 크기', { city: 3 }),
    option('눈에 띄는 디자인보다는 매일 편안한 실내', { comfort: 3 }),
    option('디자인보다 함께 탈 사람과 짐을 위한 공간', { together: 3, adventure: 1 }),
    option('조금 익숙해질 시간이 필요해도 내 취향의 디자인', { explorer: 3 }),
  ]),
};

export const tasteTypes = {
  city: { name: '가벼운 도심형 첫 차', description: '가까운 약속부터 출퇴근까지, 처음에도 다루기 부담 없는 크기와 간편함을 기대해요.', tags: ['도심 일상', '주차 편의', '간편한 사용'] },
  comfort: { name: '편안한 일상형 첫 차', description: '매일의 이동이 편안한 시간이 되길 바라요. 아늑한 좌석과 차분한 실내에 마음이 가요.', tags: ['편안한 이동', '아늑한 실내', '일상 활용'] },
  adventure: { name: '주말 탐험형 첫 차', description: '첫 차와 함께 가보고 싶은 곳이 많아요. 여행 짐과 취미용품을 담을 공간을 기대해요.', tags: ['주말 여행', '취미 활동', '짐 공간'] },
  together: { name: '함께하는 공간형 첫 차', description: '소중한 사람과 함께할 이동을 그려요. 편하게 타고 내리며 함께 앉을 공간을 중요하게 생각해요.', tags: ['동승자 배려', '여유로운 좌석', '함께하는 일상'] },
  explorer: { name: '개성 표현형 첫 차', description: '내 첫 차에서 나다운 모습을 발견하고 싶어요. 디자인과 실내 분위기, 편리한 연결 기능에 끌려요.', tags: ['나만의 디자인', '실내 분위기', '편리한 연결'] },
};
