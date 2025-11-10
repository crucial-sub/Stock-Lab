/**
 * Quant 페이지 - 동적 렌더링
 * - 클라이언트에서 데이터를 가져오도록 변경 (빌드 시 백엔드 연결 불필요)
 * - React Query를 통해 클라이언트에서 데이터를 fetch합니다
 */

import { QuantNewPageClient } from "./QuantNewPageClient";

// 동적 렌더링 강제 (빌드 시 SSR 건너뛰기)
export const dynamic = "force-dynamic";

/**
 * Quant 새 전략 페이지
 * - 클라이언트 컴포넌트에서 데이터를 fetch합니다
 */
export default function NewScriptPage() {
  return <QuantNewPageClient />;
}
