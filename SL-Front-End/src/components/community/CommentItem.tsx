export interface CommentItemProps {
  author: string;
  date: string;
  content: string;
  className?: string;
}

/**
 * 댓글 아이템 컴포넌트
 * - 작성자, 날짜, 내용 표시
 */
export function CommentItem({
  author,
  date,
  content,
  className = "",
}: CommentItemProps) {
  return (
    <div className={`flex flex-col py-4 ${className}`}>
      {/* 작성자 및 날짜 */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-base font-medium text-body">
          {author}
        </span>
        <span className="text-sm text-muted">
          {date}
        </span>
      </div>

      {/* 댓글 내용 */}
      <p className="text-base text-body">
        {content}
      </p>
    </div>
  );
}
