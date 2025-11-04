# Stock Lab Frontend

퀀트 투자 백테스트 입문자를 위한 웹 서비스의 프론트엔드 프로젝트입니다.

## 기술 스택

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **State Management**:
  - Zustand (클라이언트 상태)
  - React Query (@tanstack/react-query) (서버 상태)
- **Code Quality**: Biome (린트 & 포맷)
- **Package Manager**: pnpm 10+

## 사전 요구사항

- Node.js 20 LTS 이상
- pnpm 8 이상 (corepack enable으로 설치)

```bash
corepack enable
```

## 설치 및 실행

### 의존성 설치
```bash
pnpm install
```

### 개발 서버 실행
```bash
pnpm dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인할 수 있습니다.

## 사용 가능한 스크립트

- `pnpm dev` - 개발 서버 실행 (Turbopack 사용)
- `pnpm build` - 프로덕션 빌드
- `pnpm start` - 프로덕션 서버 실행
- `pnpm typecheck` - TypeScript 타입 체크
- `pnpm lint` - Biome 린트 검사
- `pnpm lint:fix` - Biome 린트 자동 수정
- `pnpm format` - Biome 코드 포맷팅

## 프로젝트 구조

```
sl-front-end/
├── src/
│   ├── app/                    # Next.js App Router 페이지
│   │   ├── layout.tsx         # 루트 레이아웃
│   │   ├── page.tsx           # 홈 페이지
│   │   ├── providers.tsx      # React Query Provider 래퍼
│   │   └── globals.css        # 전역 스타일
│   ├── components/            # 재사용 가능한 UI 컴포넌트
│   ├── hooks/                 # 커스텀 React 훅
│   ├── lib/                   # 유틸리티 함수 및 헬퍼
│   └── stores/                # Zustand 상태 관리
│       ├── example-store.ts   # 예제 스토어
│       └── index.ts           # 스토어 export
├── public/                    # 정적 파일
├── docs/                      # 문서
├── tailwind.config.ts         # Tailwind 설정
├── tsconfig.json              # TypeScript 설정
├── biome.json                 # Biome 설정
└── package.json
```