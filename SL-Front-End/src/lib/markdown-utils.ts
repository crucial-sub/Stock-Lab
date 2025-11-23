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

  // 0-1. 단일 별표로 시작하는 불릿(* )을 대시 불릿(- )으로 정규화 (헤딩이나 굵게(**)는 제외)
  normalized = normalized.replace(/^[ \t]*\*(\s+)/gm, "-$1");
  // 0-2. 도트/중괄호 불릿도 대시로 변환
  normalized = normalized.replace(/^[ \t]*[•·](\s+)/gm, "-$1");

  // 0-3. "성장성: ..." 같이 콜론으로 시작하는 설명을 불릿 + 굵게 구간으로 변환
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

  // 6-0. 탭/파이프 기반 테이블 행 정규화
  normalized = normalized
    .split("\n")
    .map((line) => {
      const raw = line;
      const trimmed = raw.trim();
      if (!trimmed) return raw;

      const removeBullets = trimmed.replace(/^[*-]+\s*/, "").trim();
      const sanitizeToken = (token: string) =>
        token.replace(/^\*+|\*+$/g, "").replace(/^_+|_+$/g, "").trim();

      const convertCells = (parts: string[]) => {
        const cleaned = parts.map((part) => sanitizeToken(part));
        while (cleaned.length && cleaned[0] === "") cleaned.shift();
        while (cleaned.length && cleaned[cleaned.length - 1] === "") cleaned.pop();
        if (cleaned.length < 2) return null;
        return `| ${cleaned.join(" | ")} |`;
      };

      if (removeBullets.includes("\t")) {
        const tabParts = removeBullets.split("\t");
        const converted = convertCells(tabParts);
        if (converted) return converted;
      }

      if (removeBullets.includes("|")) {
        const pipeParts = removeBullets.split("|");
        const converted = convertCells(pipeParts);
        if (converted) return converted;
      }

      return raw;
    })
    .join("\n");

  // 6-0-a. 한 줄에 여러 행이 붙은 테이블을 행 단위로 분리하고 헤더를 추출
  {
    const lines = normalized.split("\n");
    const expanded: string[] = [];

    for (const line of lines) {
      const pipeCount = (line.match(/\|/g) || []).length;
      if (pipeCount < 6) {
        expanded.push(line);
        continue;
      }

      let tokens = line
        .split("|")
        .map((t) => t.replace(/^\*+|\*+$/g, "").replace(/^_+|_+$/g, "").trim())
        .filter((t) => t.length > 0);
      if (!tokens.length) {
        expanded.push(line);
        continue;
      }

      let heading: string | null = null;
      if (/^#{1,6}\s*/.test(tokens[0])) {
        heading = tokens.shift()!.replace(/^#{1,6}\s*/, "").trim();
      }

      const dashIdx = tokens.findIndex((t) => /^-+$/.test(t.replace(/\s+/g, "")));
      const colCount = Math.max(
        2,
        Math.min(
          6,
          dashIdx > 1
            ? dashIdx
            : tokens.length >= 3
              ? Math.min(6, tokens.length)
              : tokens.length
        )
      );

      const header = tokens.slice(0, colCount);
      const bodyStart = dashIdx >= 0 ? dashIdx + colCount : colCount;
      const bodyTokens = tokens
        .slice(bodyStart)
        .filter((t) => !/^-+$/.test(t.replace(/\s+/g, "")));

      if (heading) {
        expanded.push(`### ${heading}`);
      }

      if (header.length) {
        expanded.push(`| ${header.join(" | ")} |`);
        expanded.push(`| ${Array(colCount).fill("---").join(" | ")} |`);
        for (let i = 0; i < bodyTokens.length; i += colCount) {
          const row = bodyTokens.slice(i, i + colCount);
          if (row.length === 0) continue;
          expanded.push(`| ${row.join(" | ")} |`);
        }
        continue;
      }

      expanded.push(line);
    }

    normalized = expanded.join("\n");
  }

  // 6-0. 파이프(|) 기반 표가 한 줄에 붙어있는 경우 줄바꿈 추가
  normalized = normalized.replace(/((?:\|\s*[^|\n]+\s*){2,}\|)/g, (match, _row, offset, original) => {
    const prevChar = offset > 0 ? original[offset - 1] : "\n";
    const needsNewline = prevChar !== "\n";
    return `${needsNewline ? "\n" : ""}${match.trim()}`;
  });
  // 표 행이 공백만 사이에 두고 이어지는 경우 개행으로 분리
  normalized = normalized.replace(/(\|[^\n]+?\|)\s+(?=\|)/g, "$1\n");

  // 6-0-0. 테이블 행 전체를 감싼 이탤릭/볼드 마크업 제거
  normalized = normalized.replace(/^[ \t]*[*_]+(\s*\|.*\|)\s*[*_]+[ \t]*$/gm, "$1");

  // 6-0-1. 표 블록 구성 및 헤더 구분선 보정
  const tableRowRegex = /^[*_]?\s*\|\s*[^|]+\|\s*[*_]?$/;
  const tableLines = normalized.split("\n");
  const rebuiltLines: string[] = [];
  let tableBuffer: string[] = [];
  let inTableBlock = false;

  const flushTableBuffer = () => {
    if (!tableBuffer.length) return;
    const cleaned = tableBuffer.filter((line) => line.trim().length > 0);
    if (!cleaned.length) {
      tableBuffer = [];
      inTableBlock = false;
      return;
    }

    const headerCells = cleaned[0]
      .split("|")
      .map((cell) => cell.trim())
      .filter((cell) => cell.length > 0);
    const columnCount = Math.max(2, headerCells.length);
    const separatorRow = `| ${Array(columnCount).fill("---").join(" | ")} |`;
    const secondRow = cleaned[1]?.trim() ?? "";
    const hasSeparator =
      secondRow.length > 0 &&
      secondRow
        .replace(/\s+/g, " ")
        .match(/^\|\s*:?-{3,}(\s*\|\s*:?-{3,})+\s*\|$/);

    const normalizedBuffer = hasSeparator ? cleaned : [cleaned[0], separatorRow, ...cleaned.slice(1)];

    if (rebuiltLines.length && rebuiltLines[rebuiltLines.length - 1].trim() !== "") {
      rebuiltLines.push("");
    }
    rebuiltLines.push(...normalizedBuffer);
    rebuiltLines.push("");
    tableBuffer = [];
    inTableBlock = false;
  };

  for (const line of tableLines) {
    const trimmedLine = line.trim();
    const cleanedLine = trimmedLine.replace(/^[*_]+\s*|\s*[*_]+$/g, "");

    if (tableRowRegex.test(trimmedLine) || tableRowRegex.test(cleanedLine)) {
      tableBuffer.push(cleanedLine);
      inTableBlock = true;
      continue;
    }

    if (trimmedLine === "" && inTableBlock) {
      continue;
    }

    if (inTableBlock) {
      flushTableBuffer();
    }
    rebuiltLines.push(line);
  }

  if (inTableBlock) {
    flushTableBuffer();
  }
  normalized = rebuiltLines.join("\n").replace(/\n{3,}/g, "\n\n");

  // 6-1. 내용 없는 불릿/번호 줄 제거 (깨진 리스트 정리)
  normalized = normalized
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      if (/^[-*]\s*$/.test(trimmed)) return false;
      if (/^\d+\.\s*$/.test(trimmed)) return false;
      return true;
    })
    .join("\n");

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
