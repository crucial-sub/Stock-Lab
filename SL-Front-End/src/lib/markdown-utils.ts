/**
 * 마크다운 텍스트 전처리 유틸리티
 *
 * 백엔드에서 줄바꿈 없이 마크다운을 보내는 경우,
 * 마크다운 구문 앞뒤에 줄바꿈을 추가하여 올바르게 파싱되도록 함
 */

/**
 * 마크다운 헤딩과 리스트에 줄바꿈 추가 + 번호 리스트 재정렬
 *
 * @param content 원본 마크다운 텍스트
 * @returns 줄바꿈이 추가되고 번호가 재정렬된 마크다운 텍스트
 */
export function normalizeMarkdown(content: string): string {
  if (!content) return content;

  let normalized = content;

  // 1. 헤딩(## ) 앞에 줄바꿈 2개 추가 (단, 맨 앞은 제외)
  normalized = normalized.replace(/([^\n])(\s*)(#{1,6}\s+)/g, "$1\n\n$3");

  // 2. 리스트(- ) 앞에 줄바꿈 추가 (단, 이미 줄바꿈이 있으면 제외)
  normalized = normalized.replace(/([^\n])([-*]\s+)/g, "$1\n$2");

  // 3. 빈 헤딩(### 뒤에 텍스트 없음) 제거 - 리스트 분리 방지
  // 먼저 ###만 있는 줄을 제거
  normalized = normalized.replace(/^#{1,6}\s*$/gm, "");
  // 그리고 연속된 줄바꿈 정리
  normalized = normalized.replace(/\n{3,}/g, "\n\n");

  // 4. 번호 리스트(1. ) 앞에 줄바꿈 추가
  normalized = normalized.replace(/([^\n])(\d+\.\s+)/g, "$1\n$2");

  // 5. 번호 리스트 재정렬: 헤딩을 기준으로 각 섹션의 번호를 1, 2, 3, 4로 수정
  console.log("=== 번호 재정렬 전 ===");
  console.log(normalized.substring(0, 500));

  // 헤딩으로 섹션 분할
  const sections = normalized.split(/(#{1,6}\s+[^\n]+)/);
  console.log("섹션 개수:", sections.length);

  const processedSections = sections.map((section, idx) => {
    console.log(`섹션 ${idx}:`, section.substring(0, 100));
    // 헤딩이 아닌 섹션에서만 리스트 번호 재정렬
    if (!section.match(/^#{1,6}\s+/)) {
      let counter = 0;
      const processed = section.replace(/^\d+\.\s+/gm, (match) => {
        counter++;
        console.log(`번호 교체: ${match} → ${counter}. `);
        return `${counter}. `;
      });
      return processed;
    }
    return section;
  });

  normalized = processedSections.join('');
  console.log("=== 번호 재정렬 후 ===");
  console.log(normalized.substring(0, 500));

  // 6. 연속된 줄바꿈 정리 (3개 이상의 줄바꿈은 2개로)
  normalized = normalized.replace(/\n{3,}/g, "\n\n");

  // 7. 맨 앞의 줄바꿈 제거
  normalized = normalized.replace(/^\n+/, "");

  return normalized;
}

/**
 * 디버깅용: 마크다운 정규화 전후 비교
 */
export function debugMarkdown(content: string): void {
  console.log("=== 마크다운 정규화 디버깅 ===");
  console.log("원본:", JSON.stringify(content.substring(0, 200)));
  const normalized = normalizeMarkdown(content);
  console.log("정규화 후:", JSON.stringify(normalized.substring(0, 200)));
  console.log("줄바꿈 개수:", (normalized.match(/\n/g) || []).length);
}
