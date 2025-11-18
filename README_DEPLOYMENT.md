# 📚 배포 가이드 모음

## 📖 가이드 선택

### 🟢 간단한 배포 (단일 EC2 - 로컬 DB/Redis)
**대상**: MVP, 테스트, 소규모 서비스 (사용자 50명 이하)
**비용**: ~$10/월
**Auto Scaling**: ❌ 불가능
**가이드**: 이 가이드는 현재 지원 안함 (RDS 버전 권장)

---

### 🟡 프로덕션 배포 (EC2 + RDS + ElastiCache)
**대상**: 실제 서비스, 확장 가능한 구조
**비용**: ~$45/월 (Free Tier: ~$15/월)
**Auto Scaling**: ✅ 가능
**가이드**: **`QUICK_START_EC2.md`** ⭐ 추천!

**장점**:
- ✅ Auto Scaling 가능
- ✅ 데이터 일관성 보장
- ✅ 자동 백업, 고가용성
- ✅ 성능 최적화

---

### 🔴 Auto Scaling 구성 (ALB + ASG + RDS + ElastiCache)
**대상**: 대규모 서비스 (사용자 100명 이상)
**비용**: ~$100/월
**Auto Scaling**: ✅ 완전 지원
**가이드**: **`AUTO_SCALING_ISSUES.md`**

**장점**:
- ✅ 자동 확장 (트래픽 대응)
- ✅ 무중단 배포
- ✅ 고가용성 (Multi-AZ)

---

## 🚀 빠른 시작

### 1. AWS RDS + ElastiCache 배포 (권장)
```bash
# 1. QUICK_START_EC2.md 읽기
cat QUICK_START_EC2.md

# 2. AWS 콘솔에서 RDS, ElastiCache 생성

# 3. EC2에서 프로젝트 Clone
git clone <repo> Stock-Lab-Demo
cd Stock-Lab-Demo

# 4. 환경 변수 설정
cp .env.ec2 .env
cp SL-Back-end/.env.ec2 SL-Back-end/.env

# 5. RDS, ElastiCache 엔드포인트 수정
nano .env
nano SL-Back-end/.env

# 6. 배포 실행
./deploy-rds.sh
```

---

## 📁 배포 관련 파일

| 파일명 | 설명 | 용도 |
|--------|------|------|
| **QUICK_START_EC2.md** | RDS + ElastiCache 빠른 배포 가이드 | ⭐ 가장 중요 |
| **AUTO_SCALING_ISSUES.md** | Auto Scaling 구성 및 문제 해결 | Auto Scaling 시 필독 |
| **EC2_DEPLOYMENT_GUIDE.md** | 상세 배포 가이드 (전체) | 트러블슈팅 참고 |
| **.env.ec2** | 루트 환경 변수 템플릿 | EC2 IP 설정 |
| **SL-Back-end/.env.ec2** | 백엔드 환경 변수 템플릿 | RDS, ElastiCache 설정 |
| **docker-compose.ec2.yml** | 프로덕션용 Docker Compose | RDS/ElastiCache 사용 |
| **deploy-rds.sh** | 자동 배포 스크립트 | 배포 자동화 |

---

## 🎯 배포 시나리오별 가이드

### 시나리오 1: 처음 배포하는 경우
```
1. QUICK_START_EC2.md 읽기
2. AWS RDS, ElastiCache 생성
3. EC2에서 deploy-rds.sh 실행
4. 브라우저에서 http://<EC2_IP>:3000 접속
```

### 시나리오 2: Auto Scaling 추가하려는 경우
```
1. AUTO_SCALING_ISSUES.md 읽기
2. 현재 구조가 RDS + ElastiCache 사용 중인지 확인
3. ALB 생성
4. Auto Scaling Group 생성
5. Lambda + EventBridge 스케줄러 분리
```

### 시나리오 3: 로컬에서 RDS로 마이그레이션
```
1. AWS RDS, ElastiCache 생성
2. 로컬 DB 백업
   pg_dump -U stocklabadmin -d stock_lab_investment_db > backup.sql
3. RDS로 복원
   psql -h <RDS_ENDPOINT> -U stocklabadmin -d stock_lab_investment_db < backup.sql
4. .env 파일 수정 (RDS, ElastiCache 엔드포인트)
5. docker-compose -f docker-compose.ec2.yml up -d
```

---

## 🔧 환경 변수 설정 요약

### `.env` (루트)
```bash
NEXT_PUBLIC_API_BASE_URL=http://YOUR_EC2_IP:8000/api/v1
```

### `SL-Back-end/.env`
```bash
# RDS
DATABASE_URL=postgresql+asyncpg://USER:PASS@RDS_ENDPOINT:5432/stock_lab_investment_db

# ElastiCache
REDIS_URL=redis://ELASTICACHE_ENDPOINT:6379/0

# CORS
BACKEND_CORS_ORIGINS=["http://YOUR_EC2_IP:3000"]
```

---

## 💰 비용 비교

| 구성 | 월 비용 | Auto Scaling | 고가용성 |
|------|---------|--------------|----------|
| 로컬 DB/Redis | ~$10 | ❌ | ❌ |
| RDS + ElastiCache | ~$45 | ✅ | ✅ |
| ALB + ASG + RDS | ~$100 | ✅✅ | ✅✅ |

---

## 🚨 주의사항

### ❌ 하지 말아야 할 것
1. **로컬 DB/Redis로 Auto Scaling 설정** → 데이터 불일치, 중복 실행 발생
2. **RDS 비밀번호 GitHub에 커밋** → 보안 위험
3. **프로덕션에서 DEBUG=true** → 성능 저하, 보안 위험

### ✅ 해야 할 것
1. **RDS + ElastiCache 사용** → Auto Scaling 가능
2. **환경 변수 안전하게 관리** → AWS Secrets Manager 권장
3. **정기 백업 설정** → RDS 자동 백업 활성화
4. **모니터링 설정** → CloudWatch 알람 설정

---

## 📞 문제 발생 시

### 1. RDS 연결 안됨
- 보안 그룹 확인 (EC2 → RDS 5432 포트 허용)
- 엔드포인트 확인 (DATABASE_URL)
- 비밀번호 확인

### 2. ElastiCache 연결 안됨
- 보안 그룹 확인 (EC2 → ElastiCache 6379 포트 허용)
- VPC 확인 (같은 VPC 내부)
- 엔드포인트 확인 (REDIS_URL)

### 3. CORS 에러
- BACKEND_CORS_ORIGINS에 프론트엔드 URL 추가
- 백엔드 재시작

---

## 📖 추가 자료

- [AWS RDS 가이드](https://docs.aws.amazon.com/rds/)
- [AWS ElastiCache 가이드](https://docs.aws.amazon.com/elasticache/)
- [Docker Compose 문서](https://docs.docker.com/compose/)

---

**문제가 해결되지 않으면**: 각 가이드 문서의 "문제 해결" 섹션 참고
