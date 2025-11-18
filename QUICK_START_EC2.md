# ⚡ EC2 빠른 배포 가이드 (5분 완성)

## 1️⃣ EC2에서 프로젝트 Clone

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 Clone
git clone <your-repo-url> Stock-Lab-Demo
cd Stock-Lab-Demo
```

---

## 2️⃣ 환경 변수 설정 (단 2개 파일만!)

### 📄 파일 1: 루트 `.env`
```bash
# .env.ec2를 .env로 복사
cp .env.ec2 .env

# EC2 퍼블릭 IP로 수정
nano .env
```

**수정할 곳 (딱 1줄):**
```bash
# 19번째 줄: localhost를 EC2 IP로 변경
NEXT_PUBLIC_API_BASE_URL=http://YOUR_EC2_IP:8000/api/v1
```

예시:
```bash
NEXT_PUBLIC_API_BASE_URL=http://3.38.123.456:8000/api/v1
```

**저장: Ctrl+O → Enter → Ctrl+X**

---

### 📄 파일 2: 백엔드 `.env`
```bash
# .env.ec2를 .env로 복사
cp SL-Back-end/.env.ec2 SL-Back-end/.env

# CORS 설정 수정
nano SL-Back-end/.env
```

**수정할 곳 (딱 1줄):**
```bash
# 42번째 줄: localhost를 EC2 IP로 변경
BACKEND_CORS_ORIGINS=["http://YOUR_EC2_IP:3000"]
```

예시:
```bash
BACKEND_CORS_ORIGINS=["http://3.38.123.456:3000"]
```

**저장: Ctrl+O → Enter → Ctrl+X**

---

## 3️⃣ Docker 실행

```bash
# 자동 배포 스크립트 실행
./deploy.sh
```

**또는 수동 실행:**
```bash
docker-compose up -d --build
```

---

## 4️⃣ 접속 확인

### 브라우저에서:
- **프론트엔드**: `http://<EC2_IP>:3000`
- **백엔드 API 문서**: `http://<EC2_IP>:8000/docs`

### 터미널에서:
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

---

## 🔥 그게 다야!

**수정한 파일:**
1. `.env` - 1줄 (NEXT_PUBLIC_API_BASE_URL)
2. `SL-Back-end/.env` - 1줄 (BACKEND_CORS_ORIGINS)

**실행:**
```bash
./deploy.sh
```

**완료!** 🎉

---

## 📝 EC2 IP 확인하는 법

### EC2 콘솔에서:
1. EC2 대시보드 → 인스턴스 클릭
2. "퍼블릭 IPv4 주소" 복사

### 터미널에서:
```bash
curl http://checkip.amazonaws.com
```

---

## 🛠️ 유용한 명령어

```bash
# 재시작
docker-compose restart

# 중지
docker-compose down

# 로그 보기
docker-compose logs -f backend
docker-compose logs -f frontend

# 컨테이너 상태
docker-compose ps
```

---

## ⚠️ 보안 그룹 설정 확인

EC2 인바운드 규칙에 다음 포트가 열려있어야 합니다:
- **3000** (Frontend)
- **8000** (Backend)
- **22** (SSH)

---

## 🚨 문제 해결

### "포트가 이미 사용 중입니다"
```bash
# 기존 프로세스 종료
sudo netstat -tulpn | grep :3000
sudo kill -9 <PID>
```

### "CORS 에러"
```bash
# CORS 설정 다시 확인
nano SL-Back-end/.env
# BACKEND_CORS_ORIGINS에 EC2 IP 확인
docker-compose restart backend
```

### "API 호출 안됨"
```bash
# .env 파일 확인
cat .env | grep NEXT_PUBLIC_API_BASE_URL
# EC2 IP가 맞는지 확인
# 틀리면 다시 수정 후 재시작
nano .env
docker-compose restart frontend
```

---

## 💡 더 자세한 가이드

전체 문서: `EC2_DEPLOYMENT_GUIDE.md` 참고
