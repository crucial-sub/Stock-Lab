/**
 * 공통 마크다운 컴포넌트
 *
 * Streaming/정적 렌더러가 공유해 일관된 시인성과 가독성을 제공합니다.
 * 큰 여백, 명확한 대비, 브랜드 컬러 포인트에 집중했습니다.
 */

import type { Components } from "react-markdown";

export const markdownComponents: Partial<Components> = {
  // 제목
  h1: ({ children }) => (
    <h1 className="text-[1.75rem] font-semibold text-body leading-snug mt-8 mb-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-[1.5rem] font-semibold text-body leading-snug mt-6 mb-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-[1.25rem] font-semibold text-body leading-snug mt-4 mb-0">
      {children}
    </h3>
  ),

  // 단락
  p: ({ children }) => (
    <p className="text-[1rem] leading-7 text-[#1F2937] m-0">{children}</p>
  ),

  // 리스트
  ul: ({ children }) => (
    <ul className="list-disc list-inside text-[1rem] text-[#1F2937] ml-4 p-0">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-inside text-[1rem] text-[#1F2937] ml-4 p-0">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-7 m-0 p-0">{children}</li>,

  // 강조
  strong: ({ children }) => (
    <strong className="font-bold text-brand-purple">{children}</strong>
  ),
  em: ({ children }) => <em className="italic text-[#374151]">{children}</em>,

  // 코드
  code: ({ node, children, ...props }) => {
    const isInline = !node || node.position?.start.line === node.position?.end.line;
    return isInline ? (
      <code
        className="bg-[#F5F5FF] text-brand-purple px-1.5 py-0.5 rounded-[6px] text-[0.9rem] font-mono"
        {...props}
      >
        {children}
      </code>
    ) : (
      <code
        className="block bg-[#0E1525] text-[#EDE9FE] border border-[#4C1D95]/40 p-4 rounded-xl overflow-x-auto text-[0.95rem] font-mono leading-[1.6]"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }) => <pre className="bg-transparent p-0 m-0 mb-4">{children}</pre>,

  // 인용구
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-brand-purple/40 bg-brand-purple/5 pl-0 pr-4 py-3 rounded-r-xl text-[#374151] italic my-0">
      {children}
    </blockquote>
  ),

  // 링크
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-brand-purple font-medium underline decoration-1 underline-offset-2 hover:opacity-80 transition"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),

  // 테이블
  table: ({ children }) => (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm text-gray-800 border border-[#E5E7EB] rounded-xl overflow-hidden">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-[#F3F4F6] text-[#111827] font-semibold">{children}</thead>
  ),
  tbody: ({ children }) => (
    <tbody className="divide-y divide-[#E5E7EB]">{children}</tbody>
  ),
  tr: ({ children }) => <tr>{children}</tr>,
  th: ({ children }) => (
    <th className="py-3 pr-3 pl-0 text-xs font-semibold tracking-wide uppercase">{children}</th>
  ),
  td: ({ children }) => (
    <td className="py-2 pr-4 pl-0 text-sm text-[#1F2937]">{children}</td>
  ),

  // 구분선
  hr: () => <hr className="my-8 border-gray-200" />,
};

// 공통 prose 클래스
export const markdownProseClasses =
  "prose prose-base max-w-none text-[#1F2937] leading-7 prose-headings:font-semibold prose-headings:text-body prose-p:m-0 prose-li:leading-7 prose-strong:text-brand-purple prose-code:text-[0.95rem] prose-code:font-mono prose-blockquote:border-brand-purple/50 prose-blockquote:bg-brand-purple/5 prose-blockquote:text-[#374151] m-0";
