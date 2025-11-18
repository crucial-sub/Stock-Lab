/**
 * 공통 마크다운 컴포넌트 정의
 *
 * MarkdownRenderer와 StreamingMarkdownRenderer에서 공통으로 사용하는
 * 마크다운 렌더링 컴포넌트들을 정의합니다.
 *
 * 이점:
 * - 중복 코드 제거 (~5KB 번들 크기 감소)
 * - 일관된 스타일 유지
 * - 유지보수성 향상
 */

import type { Components } from "react-markdown";

/**
 * ReactMarkdown의 Components 타입에 맞는 공통 컴포넌트 정의
 * GPT 스타일: 깔끔하고 읽기 쉬운 마크다운 렌더링
 */
export const markdownComponents: Partial<Components> = {
  // 제목 스타일
  h1: ({ children }) => (
    <h1 className="text-2xl font-bold mt-6 mb-4 text-gray-900">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-xl font-semibold mt-5 mb-3 text-gray-900">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-lg font-semibold mt-4 mb-2 text-gray-900">
      {children}
    </h3>
  ),

  // 단락 스타일
  p: ({ children }) => (
    <p className="mb-4 text-gray-800 leading-7">{children}</p>
  ),

  // 리스트 스타일
  ul: ({ children }) => (
    <ul className="list-disc list-outside ml-6 mb-4 space-y-2">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-outside ml-6 mb-4 space-y-2">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li className="text-gray-800 leading-7">{children}</li>
  ),

  // 강조 스타일
  strong: ({ children }) => (
    <strong className="font-semibold text-gray-900">
      {children}
    </strong>
  ),
  em: ({ children }) => (
    <em className="italic text-gray-700">{children}</em>
  ),

  // 코드 블록 스타일
  code: ({ inline, children }) =>
    inline ? (
      <code className="bg-gray-100 text-pink-600 px-1.5 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    ) : (
      <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
        {children}
      </code>
    ),
  pre: ({ children }) => (
    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4">
      {children}
    </pre>
  ),

  // 인용구 스타일
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700 my-4">
      {children}
    </blockquote>
  ),

  // 링크 스타일
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-blue-600 hover:text-blue-800 underline"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),

  // 테이블 스타일
  table: ({ children }) => (
    <div className="overflow-x-auto my-4">
      <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-gray-50">{children}</thead>
  ),
  tbody: ({ children }) => (
    <tbody className="bg-white divide-y divide-gray-200">
      {children}
    </tbody>
  ),
  tr: ({ children }) => <tr>{children}</tr>,
  th: ({ children }) => (
    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2 text-sm text-gray-800">
      {children}
    </td>
  ),

  // 수평선 스타일
  hr: () => <hr className="my-6 border-gray-200" />,
};

/**
 * 마크다운 렌더링 공통 prose 클래스
 * Tailwind Typography 플러그인 활용
 */
export const markdownProseClasses =
  "prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-gray-900 prose-p:text-gray-800 prose-p:leading-7 prose-li:text-gray-800 prose-li:leading-7 prose-strong:text-gray-900 prose-strong:font-semibold prose-code:text-pink-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100";
