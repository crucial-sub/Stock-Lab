-- companies.industry 값을 theme_name_kor로 통일
-- 백테스트 테마 매칭 문제 해결

UPDATE companies
SET industry = '전기 / 가스 / 수도'
WHERE industry = '전기·가스·수도';

UPDATE companies
SET industry = '농업 / 임업 / 어업'
WHERE industry = '농업, 임업 및 어업';

UPDATE companies
SET industry = '전기 / 전자'
WHERE industry = '전기·전자';

UPDATE companies
SET industry = 'IT서비스'
WHERE industry = 'IT 서비스';

UPDATE companies
SET industry = '기계 / 장비'
WHERE industry = '기계·장비';

UPDATE companies
SET industry = '섬유 / 의류'
WHERE industry = '섬유·의류';

UPDATE companies
SET industry = '오락 / 문화'
WHERE industry = '오락·문화';

UPDATE companies
SET industry = '운송 / 창고'
WHERE industry = '운송·창고';

UPDATE companies
SET industry = '종이 / 목재'
WHERE industry = '종이·목재';

UPDATE companies
SET industry = '의료 / 정밀기기'
WHERE industry = '의료·정밀기기';

UPDATE companies
SET industry = '출판 / 매체 복제'
WHERE industry = '출판·매체복제';

UPDATE companies
SET industry = '음식료 / 담배'
WHERE industry = '음식료·담배';

UPDATE companies
SET industry = '기타 금융'
WHERE industry = '기타금융';

UPDATE companies
SET industry = '기타 제조'
WHERE industry = '기타제조';

UPDATE companies
SET industry = '운송장비 / 부품'
WHERE industry = '운송장비·부품';

UPDATE companies
SET industry = '일반 서비스'
WHERE industry = '일반서비스';

-- 확인
SELECT DISTINCT industry, COUNT(*) as count
FROM companies
WHERE industry IS NOT NULL
GROUP BY industry
ORDER BY industry;
