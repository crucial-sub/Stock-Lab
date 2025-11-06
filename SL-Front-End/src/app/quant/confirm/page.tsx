/**
 * 최종 조건 확인 페이지 (서버 컴포넌트)
 * - 사용자가 설정한 모든 백테스트 조건을 최종 확인
 * - 백테스트 실행 버튼을 통해 서버로 요청 전송
 */

import { QuantConfirmPageClient } from "./QuantConfirmPageClient";

/**
 * 최종 조건 확인 페이지
 * - 별도의 prefetch가 필요 없으므로 서버 컴포넌트에서 바로 클라이언트 컴포넌트 렌더링
 */
export default function QuantConfirmPage() {
  return <QuantConfirmPageClient />;
}
