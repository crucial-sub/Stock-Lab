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

  // 0. 우선 백엔드에서 이스케이프된 줄바꿈/불릿을 원상복구
  let normalized = content
    .replace(/\\n/g, "\n")
    .replace(/\\t/g, "\t")
    .replace(/\\([*_\\-])/g, "$1"); // \*, \_, \- → 원문

  // 0-1. 굵은 제목(**제목**) 다음에 오는 불릿/내용이 한 줄에 붙어 있을 때 개행 추가
  normalized = normalized.replace(/(\*\*[^*\n]+?\*\*)\s*-\s*/g, "$1\n- ");
  normalized = normalized.replace(/([^\n])(\*\*[^*\n]+?\*\*)/g, "$1\n\n$2");

  // 0-2. 단일 별표로 시작하는 불릿(* )을 대시 불릿(- )으로 정규화 (헤딩이나 굵게(**)는 제외)
  normalized = normalized.replace(/^[ \t]*\*(\s+)/gm, "-$1");
  // 0-3. 도트/중괄호 불릿도 대시로 변환
  normalized = normalized.replace(/^[ \t]*[•·](\s+)/gm, "-$1");

  // 0-4. 섹션 제목을 단일 별표로 감싼 경우(*제목*) 또는 끝에만 별표가 붙은 경우(제목*)를 굵게 헤더로 변환
  normalized = normalized.replace(/^[ \t]*\*([^*\n]+)\*[ \t]*$/gm, "**$1**");
  normalized = normalized.replace(/^[ \t]*([^*\n]+)\*[ \t]*$/gm, "**$1**");
  // 제목 앞뒤로 빈 줄 추가 (이미 있는 경우 중복 제거)
  normalized = normalized.replace(/([^\n])(\n\*\*[^\n]+\*\*\n)/g, "$1\n\n$2");
  normalized = normalized.replace(/(\n\*\*[^\n]+\*\*\n)([^\n])/g, "$1\n$2");

  // 0-5. "성장성: ..." 같이 콜론으로 시작하는 설명을 불릿 + 굵게 구간으로 변환
  normalized = normalized.replace(/^[ \t]*([A-Za-z가-힣0-9][^:\n]{0,40}):\s+/gm, "- **$1** ");

  // 1. 헤딩(## ) 앞에 줄바꿈 2개 추가 (단, 맨 앞은 제외)
  normalized = normalized.replace(/([^\n])(\s*)(#{1,6}\s+)/g, "$1\n\n$3");

  // 2. 리스트(- ) 앞에 줄바꿈 추가 (단, 이미 줄바꿈이 있으면 제외)
  normalized = normalized.replace(/([^\n])([-*]\s+)/g, "$1\n$2");

  // 3. 번호 리스트(1. ) 앞에 줄바꿈 추가
  normalized = normalized.replace(/([^\n])(\d+\.\s+)/g, "$1\n$2");

  // 4. 빈 헤딩 제거 (###만 있고 뒤에 텍스트 없음)
  normalized = normalized.replace(/\n#{1,6}\s*\n/g, "\n");

  // 5. 줄 단위로 분석하여 번호 리스트 정리
  const lines = normalized.split('\n');
  const processedLines: string[] = [];
  let inOrderedList = false;
  let listCounter = 0;
  let listItemContent: string[] = []; // 현재 리스트 항목의 내용 (여러 줄일 수 있음)

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trim();

    // 의미 있는 헤딩 (텍스트가 있는 헤딩)
    if (/^#{1,6}\s+.+/.test(trimmedLine)) {
      // 이전 리스트 항목이 있으면 추가
      if (listItemContent.length > 0) {
        processedLines.push(...listItemContent);
        listItemContent = [];
      }
      // 헤딩을 만나면 리스트 종료
      inOrderedList = false;
      listCounter = 0;
      processedLines.push(line);
      continue;
    }

    // 번호 리스트 항목인지 확인
    const orderedListMatch = trimmedLine.match(/^(\d+)\.\s+(.+)$/);

    if (orderedListMatch) {
      // 이전 리스트 항목이 있으면 추가 (빈 줄 없이)
      if (listItemContent.length > 0) {
        processedLines.push(...listItemContent);
        listItemContent = [];
      }

      // 새로운 번호 리스트 항목 시작
      if (!inOrderedList) {
        inOrderedList = true;
        listCounter = 0;
      }
      listCounter++;

      // 올바른 번호로 재정렬
      const indent = line.match(/^\s*/)?.[0] || '';
      listItemContent.push(`${indent}${listCounter}. ${orderedListMatch[2]}`);
    } else if (inOrderedList && /^[-*]\s+/.test(trimmedLine)) {
      // 번호 리스트 중 불릿 리스트 - 들여쓰기 추가 (하위 항목으로 만듦)
      listItemContent.push(`   ${trimmedLine}`); // 3칸 들여쓰기
    } else if (inOrderedList && trimmedLine !== '') {
      // 번호 리스트 중이고 빈 줄이 아니면 현재 리스트 항목의 연속된 내용
      listItemContent.push(line);
    } else if (inOrderedList && trimmedLine === '') {
      // 번호 리스트 중간의 빈 줄 - 무시 (리스트가 끊기지 않도록)
      continue;
    } else {
      // 번호 리스트가 아닌 일반 내용
      if (listItemContent.length > 0) {
        processedLines.push(...listItemContent);
        listItemContent = [];
      }
      inOrderedList = false;
      listCounter = 0;
      processedLines.push(line);
    }
  }

  // 마지막 리스트 항목 추가
  if (listItemContent.length > 0) {
    processedLines.push(...listItemContent);
  }

  normalized = processedLines.join('\n');

  // 6. 연속된 줄바꿈 정리 (3개 이상의 줄바꿈은 2개로)
  normalized = normalized.replace(/\n{3,}/g, "\n\n");

  // 7. 맨 앞의 줄바꿈 제거
  normalized = normalized.replace(/^\n+/, "");

  return normalized;
}

/**
 * 불릿 개수를 제한하는 유틸리티 (compact 모드용)
 * - 헤더/다음 단계 등 불릿이 아닌 줄은 유지
 */
export function limitBullets(content: string, maxBullets: number = 3): string {
  if (!content) return content;

  const lines = content.split("\n");
  let bulletCount = 0;
  const kept: string[] = [];

  for (const line of lines) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith("- ")) {
      bulletCount += 1;
      if (bulletCount > maxBullets) {
        continue;
      }
    }
    kept.push(line);
  }

  return kept.join("\n");
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
