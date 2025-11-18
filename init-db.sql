-- PostgreSQL 초기화 스크립트
-- 데이터베이스는 POSTGRES_DB 환경변수로 자동 생성됨

-- 필요한 확장 기능 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 기본 스키마 확인
SELECT current_database();
