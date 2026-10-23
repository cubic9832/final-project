-- 회원 전용 첫차 취향 테스트. 기존 마이그레이션은 변경하지 않는다.
CREATE TABLE taste_test_versions (
 test_version_id BIGINT PRIMARY KEY, title VARCHAR(100) NOT NULL, version_no INT NOT NULL UNIQUE,
 question_count INT NOT NULL, status_code VARCHAR(20) NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='취향 테스트 버전';
CREATE TABLE taste_types (
 taste_type_id BIGINT PRIMARY KEY, test_version_id BIGINT NOT NULL, type_code VARCHAR(40) NOT NULL,
 type_name VARCHAR(100) NOT NULL, description TEXT NOT NULL, tags_json JSON NOT NULL, display_order INT NOT NULL,
 UNIQUE KEY uq_taste_type (test_version_id,type_code),
 FOREIGN KEY (test_version_id) REFERENCES taste_test_versions(test_version_id)
) COMMENT='취향 결과 유형';
CREATE TABLE taste_questions (
 question_id BIGINT PRIMARY KEY, test_version_id BIGINT NOT NULL, step_no INT NOT NULL,
 question_code VARCHAR(40) NOT NULL, question_text VARCHAR(500) NOT NULL, is_default BOOLEAN NOT NULL DEFAULT FALSE,
 UNIQUE KEY uq_taste_question (test_version_id,question_code),
 FOREIGN KEY (test_version_id) REFERENCES taste_test_versions(test_version_id)
) COMMENT='취향 테스트 질문';
CREATE TABLE taste_options (
 option_id BIGINT PRIMARY KEY, question_id BIGINT NOT NULL, option_code CHAR(1) NOT NULL,
 option_text VARCHAR(500) NOT NULL, display_order INT NOT NULL,
 UNIQUE KEY uq_taste_option (question_id,option_code),
 FOREIGN KEY (question_id) REFERENCES taste_questions(question_id)
) COMMENT='질문별 객관식 선택지';
CREATE TABLE taste_option_scores (
 option_id BIGINT NOT NULL, taste_type_id BIGINT NOT NULL, score INT NOT NULL,
 PRIMARY KEY(option_id,taste_type_id),
 FOREIGN KEY(option_id) REFERENCES taste_options(option_id),
 FOREIGN KEY(taste_type_id) REFERENCES taste_types(taste_type_id)
) COMMENT='선택지별 취향 점수';
CREATE TABLE taste_branch_rules (
 branch_rule_id BIGINT PRIMARY KEY, source_question_id BIGINT NOT NULL, trigger_option_id BIGINT NULL,
 next_question_id BIGINT NOT NULL, priority_no INT NOT NULL, condition_json JSON NULL,
 FOREIGN KEY(source_question_id) REFERENCES taste_questions(question_id),
 FOREIGN KEY(trigger_option_id) REFERENCES taste_options(option_id),
 FOREIGN KEY(next_question_id) REFERENCES taste_questions(question_id)
) COMMENT='다음 질문 분기 규칙';
CREATE TABLE taste_type_vehicles (
 taste_type_id BIGINT NOT NULL, vehicle_id BIGINT NOT NULL, display_order INT NOT NULL,
 PRIMARY KEY(taste_type_id,vehicle_id),
 FOREIGN KEY(taste_type_id) REFERENCES taste_types(taste_type_id),
 FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
) COMMENT='취향별 대표 차량';
CREATE TABLE user_current_tastes (
 user_id BIGINT PRIMARY KEY COMMENT '회원 ID, 회원별 최대 한 행',
 taste_type_id BIGINT NOT NULL COMMENT '현재 취향 유형 ID',
 answers_json JSON NOT NULL COMMENT '서버가 검증한 8개 질문과 선택지 ID',
 saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '명시적으로 저장할 때만 갱신',
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(taste_type_id) REFERENCES taste_types(taste_type_id)
) COMMENT='회원별 현재 취향';

INSERT INTO taste_test_versions VALUES (2,'내 첫 자동차 취향 알아보기',2,8,'PUBLISHED',CURRENT_TIMESTAMP);
INSERT INTO taste_types VALUES (1,2,'city','가벼운 도심형 첫 차','가까운 약속부터 출퇴근까지, 처음에도 다루기 부담 없는 크기와 간편함을 기대해요.','["도심 일상","주차 편의","간편한 사용"]',1);
INSERT INTO taste_types VALUES (2,2,'comfort','편안한 일상형 첫 차','매일의 이동이 편안한 시간이 되길 바라요. 아늑한 좌석과 차분한 실내에 마음이 가요.','["편안한 이동","아늑한 실내","일상 활용"]',2);
INSERT INTO taste_types VALUES (3,2,'adventure','주말 탐험형 첫 차','첫 차와 함께 가보고 싶은 곳이 많아요. 여행 짐과 취미용품을 담을 공간을 기대해요.','["주말 여행","취미 활동","짐 공간"]',3);
INSERT INTO taste_types VALUES (4,2,'together','함께하는 공간형 첫 차','소중한 사람과 함께할 이동을 그려요. 편하게 타고 내리며 함께 앉을 공간을 중요하게 생각해요.','["동승자 배려","여유로운 좌석","함께하는 일상"]',4);
INSERT INTO taste_types VALUES (5,2,'explorer','개성 표현형 첫 차','내 첫 차에서 나다운 모습을 발견하고 싶어요. 디자인과 실내 분위기, 편리한 연결 기능에 끌려요.','["나만의 디자인","실내 분위기","편리한 연결"]',5);
INSERT INTO taste_questions VALUES (1,2,1,'first-car','첫 차가 생기면 가장 먼저 해보고 싶은 일은?',TRUE);
INSERT INTO taste_options VALUES (11,1,'A','가까운 카페나 맛집을 자유롭게 찾아가기',0);
INSERT INTO taste_option_scores VALUES (11,1,2);
INSERT INTO taste_options VALUES (12,1,'B','출퇴근길을 나만의 편안한 시간으로 만들기',1);
INSERT INTO taste_option_scores VALUES (12,2,2);
INSERT INTO taste_options VALUES (13,1,'C','짐을 싣고 근교 여행이나 캠핑 떠나기',2);
INSERT INTO taste_option_scores VALUES (13,3,2);
INSERT INTO taste_options VALUES (14,1,'D','가족이나 친구를 태우고 함께 나들이하기',3);
INSERT INTO taste_option_scores VALUES (14,4,2);
INSERT INTO taste_questions VALUES (2,2,2,'daily','처음 가는 동네의 카페를 찾아갈 때, 어떤 차면 더 마음이 놓일까요?',FALSE);
INSERT INTO taste_options VALUES (21,2,'A','좁은 골목과 주차장에서도 부담 없는 작은 차',0);
INSERT INTO taste_option_scores VALUES (21,1,2);
INSERT INTO taste_options VALUES (22,2,'B','길을 잘못 들어도 차분하게 이동할 수 있는 편안한 차',1);
INSERT INTO taste_option_scores VALUES (22,2,2);
INSERT INTO taste_options VALUES (23,2,'C','구경하다 산 물건과 짐도 넉넉히 담을 수 있는 차',2);
INSERT INTO taste_option_scores VALUES (23,3,2);
INSERT INTO taste_options VALUES (24,2,'D','카페 앞에 세워두면 내 취향이 느껴지는 차',3);
INSERT INTO taste_option_scores VALUES (24,5,2);
INSERT INTO taste_questions VALUES (3,2,2,'commute','첫 차로 매일 출퇴근한다면, 가장 바라는 점은?',FALSE);
INSERT INTO taste_options VALUES (31,3,'A','회사나 집의 좁은 주차장에 넣기 편했으면 좋겠다',0);
INSERT INTO taste_option_scores VALUES (31,1,2);
INSERT INTO taste_options VALUES (32,3,'B','퇴근 후 지친 몸을 편하게 맡길 수 있으면 좋겠다',1);
INSERT INTO taste_option_scores VALUES (32,2,2);
INSERT INTO taste_options VALUES (33,3,'C','퇴근 후 운동 가방이나 취미용품도 싣고 다니고 싶다',2);
INSERT INTO taste_option_scores VALUES (33,3,2);
INSERT INTO taste_options VALUES (34,3,'D','가족이나 동료와 함께 이동할 때도 여유로우면 좋겠다',3);
INSERT INTO taste_option_scores VALUES (34,4,2);
INSERT INTO taste_questions VALUES (4,2,2,'travel','첫 차와 주말 여행을 떠날 때, 어떤 모습이 더 끌리나요?',FALSE);
INSERT INTO taste_options VALUES (41,4,'A','작은 가방 하나로 가볍게 근교를 다녀오기',0);
INSERT INTO taste_option_scores VALUES (41,1,2);
INSERT INTO taste_options VALUES (42,4,'B','편안한 실내에서 쉬엄쉬엄 먼 곳까지 이동하기',1);
INSERT INTO taste_option_scores VALUES (42,2,2);
INSERT INTO taste_options VALUES (43,4,'C','캠핑 장비나 취미용품을 싣고 새로운 곳 찾아가기',2);
INSERT INTO taste_option_scores VALUES (43,3,2);
INSERT INTO taste_options VALUES (44,4,'D','가족이나 친구들과 함께 추억 만들기',3);
INSERT INTO taste_option_scores VALUES (44,4,2);
INSERT INTO taste_questions VALUES (5,2,2,'company','함께 나들이할 때, 첫 차에서 가장 챙기고 싶은 것은?',FALSE);
INSERT INTO taste_options VALUES (51,5,'A','약속 장소와 식당 주변에서 주차하기 쉬운 크기',0);
INSERT INTO taste_option_scores VALUES (51,1,2);
INSERT INTO taste_options VALUES (52,5,'B','이동하는 동안 편하게 대화할 수 있는 실내',1);
INSERT INTO taste_option_scores VALUES (52,2,2);
INSERT INTO taste_options VALUES (53,5,'C','여러 사람의 여행 가방도 담을 수 있는 짐 공간',2);
INSERT INTO taste_option_scores VALUES (53,3,2);
INSERT INTO taste_options VALUES (54,5,'D','동승자가 편하게 타고 앉을 수 있는 좌석',3);
INSERT INTO taste_option_scores VALUES (54,4,2);
INSERT INTO taste_questions VALUES (6,2,3,'small-space','다루기 편한 첫 차를 고른다면, 공간은 어느 정도면 좋을까요?',FALSE);
INSERT INTO taste_options VALUES (61,6,'A','평소 혼자 타고 작은 가방 정도만 넣으면 충분하다',0);
INSERT INTO taste_option_scores VALUES (61,1,2);
INSERT INTO taste_options VALUES (62,6,'B','혼자 또는 둘이 편하게 앉을 수 있으면 좋겠다',1);
INSERT INTO taste_option_scores VALUES (62,2,2);
INSERT INTO taste_options VALUES (63,6,'C','크기가 조금 커져도 여행 짐은 넉넉히 담고 싶다',2);
INSERT INTO taste_option_scores VALUES (63,3,2);
INSERT INTO taste_options VALUES (64,6,'D','가끔 태울 가족이나 친구의 뒷좌석도 챙기고 싶다',3);
INSERT INTO taste_option_scores VALUES (64,4,2);
INSERT INTO taste_questions VALUES (7,2,3,'comfortable-space','첫 차 안에서 편안한 시간을 보낸다면, 무엇이 가장 중요할까요?',FALSE);
INSERT INTO taste_options VALUES (71,7,'A','필요한 기능을 쉽게 찾을 수 있는 간단한 조작부',0);
INSERT INTO taste_option_scores VALUES (71,1,2);
INSERT INTO taste_options VALUES (72,7,'B','혼자서도 아늑하게 쉴 수 있는 좌석과 분위기',1);
INSERT INTO taste_option_scores VALUES (72,2,2);
INSERT INTO taste_options VALUES (73,7,'C','여행 중 쉬거나 짐을 정리하기 좋은 여유 공간',2);
INSERT INTO taste_option_scores VALUES (73,3,2);
INSERT INTO taste_options VALUES (74,7,'D','나뿐 아니라 함께 타는 사람도 편안한 좌석',3);
INSERT INTO taste_option_scores VALUES (74,4,2);
INSERT INTO taste_questions VALUES (8,2,3,'luggage-space','첫 차에 여행 짐을 싣는다면, 어떤 짐이 가장 자주 실릴까요?',FALSE);
INSERT INTO taste_options VALUES (81,8,'A','작은 배낭이나 장보기 가방 정도',0);
INSERT INTO taste_option_scores VALUES (81,1,2);
INSERT INTO taste_options VALUES (82,8,'B','가벼운 여행 가방과 편하게 쉴 담요',1);
INSERT INTO taste_option_scores VALUES (82,2,2);
INSERT INTO taste_options VALUES (83,8,'C','부피가 큰 캠핑 장비나 야외 취미용품',2);
INSERT INTO taste_option_scores VALUES (83,3,2);
INSERT INTO taste_options VALUES (84,8,'D','함께 타는 사람들의 가방이나 유아용품',3);
INSERT INTO taste_option_scores VALUES (84,4,2);
INSERT INTO taste_questions VALUES (9,2,3,'passenger-space','첫 차의 동승자 공간은 누구를 떠올리며 고르고 싶나요?',FALSE);
INSERT INTO taste_options VALUES (91,9,'A','주로 혼자 타고, 가끔 친구 한 명이면 충분하다',0);
INSERT INTO taste_option_scores VALUES (91,1,2);
INSERT INTO taste_options VALUES (92,9,'B','연인이나 친구와 둘이 편하게 이동하고 싶다',1);
INSERT INTO taste_option_scores VALUES (92,2,2);
INSERT INTO taste_options VALUES (93,9,'C','사람도 태우고 여행 짐도 넉넉히 싣고 싶다',2);
INSERT INTO taste_option_scores VALUES (93,3,2);
INSERT INTO taste_options VALUES (94,9,'D','부모님이나 아이 등 가족의 승하차와 좌석을 챙기고 싶다',3);
INSERT INTO taste_option_scores VALUES (94,4,2);
INSERT INTO taste_questions VALUES (10,2,3,'personal-space','내 취향이 담긴 첫 차, 실용성도 하나 챙긴다면?',FALSE);
INSERT INTO taste_options VALUES (101,10,'A','좁은 곳에서도 다루기 편한 크기',0);
INSERT INTO taste_option_scores VALUES (101,1,2);
INSERT INTO taste_options VALUES (102,10,'B','매일 머물러도 편안한 운전석',1);
INSERT INTO taste_option_scores VALUES (102,2,2);
INSERT INTO taste_options VALUES (103,10,'C','해보고 싶은 활동을 담을 수 있는 짐 공간',2);
INSERT INTO taste_option_scores VALUES (103,3,2);
INSERT INTO taste_options VALUES (104,10,'D','함께 타는 사람을 위한 여유로운 좌석',3);
INSERT INTO taste_option_scores VALUES (104,4,2);
INSERT INTO taste_questions VALUES (11,2,4,'concern','처음 내 차를 운전한다고 상상하면, 가장 신경 쓰이는 것은?',FALSE);
INSERT INTO taste_options VALUES (111,11,'A','좁은 골목이나 주차장에서 차를 다루는 일',0);
INSERT INTO taste_option_scores VALUES (111,1,2);
INSERT INTO taste_options VALUES (112,11,'B','복잡한 버튼이나 기능에 익숙해지는 일',1);
INSERT INTO taste_option_scores VALUES (112,1,1);
INSERT INTO taste_option_scores VALUES (112,2,1);
INSERT INTO taste_options VALUES (113,11,'C','오래 이동할 때 피곤하지 않을지',2);
INSERT INTO taste_option_scores VALUES (113,2,2);
INSERT INTO taste_options VALUES (114,11,'D','동승자가 편하게 타고 내릴 수 있을지',3);
INSERT INTO taste_option_scores VALUES (114,4,2);
INSERT INTO taste_questions VALUES (12,2,5,'parking-support','첫 차로 주차를 연습한다면, 무엇이 가장 든든할까요?',FALSE);
INSERT INTO taste_options VALUES (121,12,'A','차 폭과 길이를 가늠하기 쉬운 작은 차체',0);
INSERT INTO taste_option_scores VALUES (121,1,2);
INSERT INTO taste_options VALUES (122,12,'B','주변 장애물과 뒤쪽을 살피는 화면·알림',1);
INSERT INTO taste_option_scores VALUES (122,1,1);
INSERT INTO taste_option_scores VALUES (122,5,1);
INSERT INTO taste_options VALUES (123,12,'C','몸을 편하게 움직이며 주변을 볼 수 있는 운전석',2);
INSERT INTO taste_option_scores VALUES (123,2,2);
INSERT INTO taste_options VALUES (124,12,'D','동승자도 여유 있게 타고 내릴 수 있는 문과 공간',3);
INSERT INTO taste_option_scores VALUES (124,4,2);
INSERT INTO taste_questions VALUES (13,2,5,'simple-controls','처음 차의 기능을 익힐 때, 어떤 방식이 더 편할 것 같나요?',FALSE);
INSERT INTO taste_options VALUES (131,13,'A','자주 쓰는 기능이 눈에 보이는 버튼으로 있는 방식',0);
INSERT INTO taste_option_scores VALUES (131,1,2);
INSERT INTO taste_options VALUES (132,13,'B','기능은 많지 않아도 필요한 것을 쉽게 찾는 방식',1);
INSERT INTO taste_option_scores VALUES (132,2,2);
INSERT INTO taste_options VALUES (133,13,'C','익숙한 휴대폰과 연결해 화면에서 사용하는 방식',2);
INSERT INTO taste_option_scores VALUES (133,5,2);
INSERT INTO taste_options VALUES (134,13,'D','동승자도 좌석과 온도를 쉽게 조절할 수 있는 방식',3);
INSERT INTO taste_option_scores VALUES (134,4,2);
INSERT INTO taste_questions VALUES (14,2,5,'long-trip','첫 장거리 나들이에서 가장 기대되는 편의는?',FALSE);
INSERT INTO taste_options VALUES (141,14,'A','쉬어갈 장소에서 주차하기 편한 크기',0);
INSERT INTO taste_option_scores VALUES (141,1,2);
INSERT INTO taste_options VALUES (142,14,'B','오래 앉아도 편안한 좌석과 조용한 실내',1);
INSERT INTO taste_option_scores VALUES (142,2,2);
INSERT INTO taste_options VALUES (143,14,'C','짐과 간식을 꺼내기 편한 수납공간',2);
INSERT INTO taste_option_scores VALUES (143,3,2);
INSERT INTO taste_options VALUES (144,14,'D','뒷좌석에서도 편하게 쉴 수 있는 여유',3);
INSERT INTO taste_option_scores VALUES (144,4,2);
INSERT INTO taste_questions VALUES (15,2,5,'passenger-support','함께 탈 사람을 위해 하나를 더 챙긴다면?',FALSE);
INSERT INTO taste_options VALUES (151,15,'A','도착한 곳에서 쉽게 주차할 수 있는 크기',0);
INSERT INTO taste_option_scores VALUES (151,1,2);
INSERT INTO taste_options VALUES (152,15,'B','실내에서 편하게 대화할 수 있는 조용한 분위기',1);
INSERT INTO taste_option_scores VALUES (152,2,2);
INSERT INTO taste_options VALUES (153,15,'C','사람들의 짐을 한 번에 실을 수 있는 트렁크',2);
INSERT INTO taste_option_scores VALUES (153,3,2);
INSERT INTO taste_options VALUES (154,15,'D','타고 내리기 편하고 앉을 공간이 넉넉한 좌석',3);
INSERT INTO taste_option_scores VALUES (154,4,2);
INSERT INTO taste_questions VALUES (16,2,6,'exterior','주차장에 서 있는 내 첫 차, 어떤 모습이면 기분이 좋을까요?',FALSE);
INSERT INTO taste_options VALUES (161,16,'A','작고 단정해서 친근한 모습',0);
INSERT INTO taste_option_scores VALUES (161,1,2);
INSERT INTO taste_options VALUES (162,16,'B','유행을 크게 타지 않는 깔끔한 모습',1);
INSERT INTO taste_option_scores VALUES (162,2,2);
INSERT INTO taste_options VALUES (163,16,'C','야외 풍경과 잘 어울리는 활동적인 모습',2);
INSERT INTO taste_option_scores VALUES (163,3,2);
INSERT INTO taste_options VALUES (164,16,'D','색상이나 디자인에서 개성이 느껴지는 모습',3);
INSERT INTO taste_option_scores VALUES (164,5,2);
INSERT INTO taste_questions VALUES (17,2,7,'interior','첫 차의 문을 열었을 때, 어떤 실내에서 지내고 싶나요?',FALSE);
INSERT INTO taste_options VALUES (171,17,'A','필요한 것만 깔끔하게 정리된 단순한 공간',0);
INSERT INTO taste_option_scores VALUES (171,1,2);
INSERT INTO taste_options VALUES (172,17,'B','따뜻한 색감과 편안한 소재가 있는 아늑한 공간',1);
INSERT INTO taste_option_scores VALUES (172,2,2);
INSERT INTO taste_options VALUES (173,17,'C','가족이나 친구와 함께 앉아도 여유로운 공간',2);
INSERT INTO taste_option_scores VALUES (173,4,2);
INSERT INTO taste_options VALUES (174,17,'D','화면과 조명에서 내 취향이 느껴지는 공간',3);
INSERT INTO taste_option_scores VALUES (174,5,2);
INSERT INTO taste_questions VALUES (18,2,8,'confirm-city','작고 다루기 편한 차에 마음이 가는 편이에요. 다른 매력과 비교하면 무엇을 우선할까요?',FALSE);
INSERT INTO taste_options VALUES (181,18,'A','짐 공간이 조금 작아도 주차하기 편한 크기',0);
INSERT INTO taste_option_scores VALUES (181,1,3);
INSERT INTO taste_options VALUES (182,18,'B','크기가 조금 커져도 매일 편안한 실내',1);
INSERT INTO taste_option_scores VALUES (182,2,3);
INSERT INTO taste_options VALUES (183,18,'C','주차 연습이 더 필요해도 여행 짐을 담는 공간',2);
INSERT INTO taste_option_scores VALUES (183,3,3);
INSERT INTO taste_options VALUES (184,18,'D','크기보다는 볼 때마다 기분 좋은 디자인',3);
INSERT INTO taste_option_scores VALUES (184,5,3);
INSERT INTO taste_questions VALUES (19,2,8,'confirm-comfort','편안한 일상을 기대하고 있어요. 첫 차에서 마지막으로 우선할 것은?',FALSE);
INSERT INTO taste_options VALUES (191,19,'A','실내가 조금 작아도 다루기 부담 없는 크기',0);
INSERT INTO taste_option_scores VALUES (191,1,3);
INSERT INTO taste_options VALUES (192,19,'B','다른 특징보다 매일 편안하게 지낼 실내',1);
INSERT INTO taste_option_scores VALUES (192,2,3);
INSERT INTO taste_options VALUES (193,19,'C','편안함만큼 중요한 여행·취미용 짐 공간',2);
INSERT INTO taste_option_scores VALUES (193,3,3);
INSERT INTO taste_options VALUES (194,19,'D','나뿐 아니라 함께 타는 사람의 편안함',3);
INSERT INTO taste_option_scores VALUES (194,4,3);
INSERT INTO taste_questions VALUES (20,2,8,'confirm-adventure','여행과 활동을 담을 공간에 관심이 있어요. 첫 차에서 더 우선할 것은?',FALSE);
INSERT INTO taste_options VALUES (201,20,'A','큰 짐은 줄이더라도 평소 주차가 편한 크기',0);
INSERT INTO taste_option_scores VALUES (201,1,3);
INSERT INTO taste_options VALUES (202,20,'B','짐 공간보다는 매일 편하게 앉을 수 있는 실내',1);
INSERT INTO taste_option_scores VALUES (202,2,3);
INSERT INTO taste_options VALUES (203,20,'C','크기가 조금 커져도 여행 장비를 담는 공간',2);
INSERT INTO taste_option_scores VALUES (203,3,3);
INSERT INTO taste_options VALUES (204,20,'D','장비보다는 함께 탈 사람의 좌석 공간',3);
INSERT INTO taste_option_scores VALUES (204,4,3);
INSERT INTO taste_questions VALUES (21,2,8,'confirm-together','함께 타는 사람을 많이 떠올렸어요. 내 첫 차를 고를 때 마지막 기준은?',FALSE);
INSERT INTO taste_options VALUES (211,21,'A','동승자는 가끔 태우니 혼자 다루기 편한 크기',0);
INSERT INTO taste_option_scores VALUES (211,1,3);
INSERT INTO taste_options VALUES (212,21,'B','큰 차보다는 혼자 또는 둘이 편하게 탈 실내',1);
INSERT INTO taste_option_scores VALUES (212,2,3);
INSERT INTO taste_options VALUES (213,21,'C','좌석만큼 여행 가방과 취미 장비를 담는 공간',2);
INSERT INTO taste_option_scores VALUES (213,3,3);
INSERT INTO taste_options VALUES (214,21,'D','크기가 조금 커져도 모두가 편하게 앉는 좌석',3);
INSERT INTO taste_option_scores VALUES (214,4,3);
INSERT INTO taste_questions VALUES (22,2,8,'confirm-explorer','나만의 디자인과 분위기에 끌리고 있어요. 실용성과 비교하면 무엇을 고를까요?',FALSE);
INSERT INTO taste_options VALUES (221,22,'A','개성보다 처음 다루기 부담 없는 크기',0);
INSERT INTO taste_option_scores VALUES (221,1,3);
INSERT INTO taste_options VALUES (222,22,'B','눈에 띄는 디자인보다는 매일 편안한 실내',1);
INSERT INTO taste_option_scores VALUES (222,2,3);
INSERT INTO taste_options VALUES (223,22,'C','디자인보다 함께 탈 사람과 짐을 위한 공간',2);
INSERT INTO taste_option_scores VALUES (223,4,3);
INSERT INTO taste_option_scores VALUES (223,3,1);
INSERT INTO taste_options VALUES (224,22,'D','조금 익숙해질 시간이 필요해도 내 취향의 디자인',3);
INSERT INTO taste_option_scores VALUES (224,5,3);
INSERT INTO taste_branch_rules VALUES (1,1,11,2,1,NULL);
INSERT INTO taste_branch_rules VALUES (2,1,12,3,2,NULL);
INSERT INTO taste_branch_rules VALUES (3,1,13,4,3,NULL);
INSERT INTO taste_branch_rules VALUES (4,1,14,5,4,NULL);
INSERT INTO taste_branch_rules VALUES (5,2,21,6,5,NULL);
INSERT INTO taste_branch_rules VALUES (6,2,22,7,6,NULL);
INSERT INTO taste_branch_rules VALUES (7,2,23,8,7,NULL);
INSERT INTO taste_branch_rules VALUES (8,2,24,10,8,NULL);
INSERT INTO taste_branch_rules VALUES (9,3,31,6,9,NULL);
INSERT INTO taste_branch_rules VALUES (10,3,32,7,10,NULL);
INSERT INTO taste_branch_rules VALUES (11,3,33,8,11,NULL);
INSERT INTO taste_branch_rules VALUES (12,3,34,9,12,NULL);
INSERT INTO taste_branch_rules VALUES (13,4,41,6,13,NULL);
INSERT INTO taste_branch_rules VALUES (14,4,42,7,14,NULL);
INSERT INTO taste_branch_rules VALUES (15,4,43,8,15,NULL);
INSERT INTO taste_branch_rules VALUES (16,4,44,9,16,NULL);
INSERT INTO taste_branch_rules VALUES (17,5,51,6,17,NULL);
INSERT INTO taste_branch_rules VALUES (18,5,52,7,18,NULL);
INSERT INTO taste_branch_rules VALUES (19,5,53,8,19,NULL);
INSERT INTO taste_branch_rules VALUES (20,5,54,9,20,NULL);
INSERT INTO taste_branch_rules VALUES (21,6,NULL,11,21,NULL);
INSERT INTO taste_branch_rules VALUES (22,7,NULL,11,22,NULL);
INSERT INTO taste_branch_rules VALUES (23,8,NULL,11,23,NULL);
INSERT INTO taste_branch_rules VALUES (24,9,NULL,11,24,NULL);
INSERT INTO taste_branch_rules VALUES (25,10,NULL,11,25,NULL);
INSERT INTO taste_branch_rules VALUES (26,11,111,12,26,NULL);
INSERT INTO taste_branch_rules VALUES (27,12,NULL,16,27,NULL);
INSERT INTO taste_branch_rules VALUES (28,11,112,13,28,NULL);
INSERT INTO taste_branch_rules VALUES (29,13,NULL,16,29,NULL);
INSERT INTO taste_branch_rules VALUES (30,11,113,14,30,NULL);
INSERT INTO taste_branch_rules VALUES (31,14,NULL,16,31,NULL);
INSERT INTO taste_branch_rules VALUES (32,11,114,15,32,NULL);
INSERT INTO taste_branch_rules VALUES (33,15,NULL,16,33,NULL);
INSERT INTO taste_branch_rules VALUES (34,16,NULL,17,34,NULL);
INSERT INTO taste_branch_rules VALUES (35,17,NULL,18,35,'{"leadingType":"city"}');
INSERT INTO taste_branch_rules VALUES (36,17,NULL,19,36,'{"leadingType":"comfort"}');
INSERT INTO taste_branch_rules VALUES (37,17,NULL,20,37,'{"leadingType":"adventure"}');
INSERT INTO taste_branch_rules VALUES (38,17,NULL,21,38,'{"leadingType":"together"}');
INSERT INTO taste_branch_rules VALUES (39,17,NULL,22,39,'{"leadingType":"explorer"}');

-- 차량을 새로 만들지 않고 기존 차량 카탈로그에서 대표 모델을 연결한다.
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 1,id,1 FROM vehicles WHERE name LIKE '%모닝%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 1,id,2 FROM vehicles WHERE name LIKE '%레이%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 2,id,1 FROM vehicles WHERE name LIKE '%아반떼%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 2,id,2 FROM vehicles WHERE name LIKE '%K5%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 3,id,1 FROM vehicles WHERE name LIKE '%스포티지%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 3,id,2 FROM vehicles WHERE name LIKE '%쏘렌토%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 4,id,1 FROM vehicles WHERE name LIKE '%쏘렌토%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 4,id,2 FROM vehicles WHERE name LIKE '%카니발%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 5,id,1 FROM vehicles WHERE name LIKE '%K5%' ORDER BY id LIMIT 1;
INSERT INTO taste_type_vehicles (taste_type_id,vehicle_id,display_order) SELECT 5,id,2 FROM vehicles WHERE name LIKE '%EV3%' ORDER BY id LIMIT 1;

