# 뉴스 탭 백엔드 연동 요구사항

아래 리스트는 `src/app/news` 페이지와 관련 컴포넌트(`NewsCard`, `NewsDetailModal`)에서 필요로 하는 데이터 구조입니다. API 설계 시 참조합니다.

## 1. 뉴스 목록 API (`GET /news`)
- **검색어**: `keyword`(string) – 상단 검색창 값.
- **테마 필터**: `themes`(string[]) – 다중 선택 태그 배열.
- **정렬/필터 옵션**: 드롭다운 값(e.g. 최신순, 인기순), 페이지/limit.

### 응답 예시 필드
- `id`: 뉴스 고유 식별자
- `title`: 메인 제목
- `subtitle`: 부제목(선택)
- `summary`: 카드에 표시할 요약 본문
- `content`: 상세 모달에 사용될 전문
- `tickerLabel`: 종목/티커명
- `themeName`: 테마 이름
- `sentiment`: `"positive" | "neutral" | "negative"`
- `pressName`: 언론사 이름
- `publishedAt`: 발행 시각(문자열 혹은 ISO)
- `link`: 원문 URL (카드/모달에서는 전체 링크 문자열을 보여주며, UI에서 `text-overflow: ellipsis` 처리)

## 2. 뉴스 상세 API (`GET /news/{id}`)
- 목록과 동일한 필드를 반환하되, `content`(카드 `summary`도 동일 본문 사용 예정, UI에서 줄임 처리), `additionalTags`, `images` 등 상세용 데이터 포함.
- 모달 최초 열릴 때 fetch하거나, 목록 응답에 이미 포함되어 있으면 재요청 없이 사용 가능.

## 3. 테마 목록 API (`GET /news/themes`) _선택_
- 현재는 하드코딩된 `newsThemes` 배열을 서버에서 내려받도록 전환 가능.
- 응답: `[{ name: string, id: string }]` 형태. “전체”는 프런트에서 추가하거나 서버에서 플래그 제공.

## 관련 파일 요약

| 파일 | 위치 | 역할 |
| --- | --- | --- |
| `types/news.ts` | `src/types` | 뉴스 도메인 타입 정의 (`NewsItem`, `NewsListParams`, `NewsSentiment`). |
| `lib/api/news.ts` | `src/lib/api` | `fetchNewsList`, `fetchNewsById` 목 API. 실제 연동 시 Axios 호출로 교체 예정. 내부 `applyFilters`로 검색/테마 필터링 처리. |
| `hooks/useNewsQuery.ts` | `src/hooks` | React Query 훅 집합. `useNewsListQuery(params)`는 목록, `useNewsDetailQuery(id)`는 상세를 조회. `newsQueryKey`로 캐시 키 관리. |
| `components/news/NewsCard.tsx` | `src/components/news` | 뉴스 카드 UI. 제목/테마/감성/요약/링크를 표시하고 `onClick`으로 모달 트리거. 링크/요약은 `text-overflow` / line clamp 처리. |
| `components/news/NewsDetailModal.tsx` | `src/components/news` | 카드 클릭 시 표시되는 상세 모달. 제목·부제·태그·본문을 보여주며 상단 고정 바/닫기 버튼/배경 딤 처리 포함. |
| `app/news/page.tsx` | `src/app/news` | 뉴스 페이지 UI. 검색·테마 필터 상태 관리, React Query 훅 호출, 카드 3×3 그리드 렌더링, 모달 오픈 로직을 담당. |

## 참고
- React Query 훅(`useNewsListQuery`, `useNewsDetailQuery`)을 통해 데이터 fetch 예정.
- 응답 구조는 `NewsCardProps` / `NewsDetailModal` prop을 그대로 채울 수 있도록 정규화하는 것이 이상적입니다. 
