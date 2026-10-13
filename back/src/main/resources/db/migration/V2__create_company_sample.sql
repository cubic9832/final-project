-- 기존 종목 API(/api/v1/companies) 예제용 테이블과 샘플 데이터
-- 컬럼명은 CompanyMapper.xml 의 SELECT 와 같아야 한다.
-- 이미 company 테이블이 있는 로컬 DB 에서도 실패하지 않도록 IF NOT EXISTS / INSERT IGNORE 를 사용한다.

CREATE TABLE IF NOT EXISTS company (
 -- 종목 코드
 code VARCHAR(20) NOT NULL PRIMARY KEY,
 -- 종목명
 name VARCHAR(100) NOT NULL,
 -- 업종 코드
 sectorCode VARCHAR(20),
 -- 업종명
 sectorName VARCHAR(100),
 -- 상장 시장
 market VARCHAR(20),
 -- 시가총액 (원)
 marketCap BIGINT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO company (code, name, sectorCode, sectorName, market, marketCap) VALUES
 ('G0001', '샘플전자', 'S01', '전기전자', 'KOSPI', 420000000000000),
 ('G0002', '샘플반도체', 'S01', '전기전자', 'KOSPI', 130000000000000),
 ('G0003', '샘플자동차', 'S02', '운수장비', 'KOSPI', 52000000000000),
 ('G0004', '샘플바이오', 'S03', '의약품', 'KOSPI', 58000000000000),
 ('G0005', '샘플화학', 'S04', '화학', 'KOSPI', 27000000000000),
 ('G0006', '샘플게임즈', 'S05', '디지털콘텐츠', 'KOSDAQ', 3200000000000),
 ('G0007', '샘플소프트', 'S06', '소프트웨어', 'KOSDAQ', 1800000000000),
 ('G0008', '샘플엔터', 'S07', '오락문화', 'KOSDAQ', 2400000000000);
