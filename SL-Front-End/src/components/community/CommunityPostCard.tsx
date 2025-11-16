import Image from "next/image";

export interface CommunityPostCardProps {
  tag: string;
  title: string;
  author: string;
  date: string;
  preview: string;
  views: number;
  likes: number;
  comments: number;
  onClick?: () => void;
  className?: string;
}

/**
 * 자유게시판 게시물 카드 컴포넌트
 * - 게시물 태그, 제목, 작성자, 날짜 표시
 * - 내용 미리보기 (2줄)
 * - 조회수, 좋아요, 댓글 수 표시
 */
export function CommunityPostCard({
  tag,
  title,
  author,
  date,
  preview,
  views,
  likes,
  comments,
  onClick,
  className = "",
}: CommunityPostCardProps) {
  // 숫자 포맷팅 (999+ 처리)
  const formatCount = (count: number): string => {
    return count > 999 ? "999+" : count.toString();
  };

  return (
    <article
      onClick={onClick}
      className={`flex w-full flex-col rounded-lg bg-surface border border-surface px-5 py-4 cursor-pointer hover:shadow-lg transition ${className}`}
    >
      {/* 태그, 제목, 작성자, 날짜 - 한 줄 */}
      <div className="flex items-center gap-3 mb-3">
        <span className="px-3 py-1 text-xs font-medium text-blue-500 bg-[#EAF5FF] border border-blue-500 rounded">
          {tag}
        </span>

        <h3 className="text-xl font-semibold text-body">
          {title}
        </h3>

        <span className="text-sm text-muted">
          by. {author}
        </span>

        <span className="text-sm text-muted">
          {date}
        </span>
      </div>

      {/* 내용 미리보기 */}
      <p className="text-sm text-muted line-clamp-2 mb-3">
        {preview}
      </p>

      {/* 통계 정보 */}
      <div className="flex items-center gap-5">
        {/* 조회수 */}
        <div className="flex items-center gap-1 ">
          <Image src="/icons/visibility.svg" width={20} height={20} alt="" />
          <span className="text-sm">
            {formatCount(views)}
          </span>
        </div>

        {/* 좋아요 */}
        <div className="flex items-center gap-1 ">
          <Image src="/icons/favorite.svg" width={20} height={20} alt="" />
          <span className="text-sm">
            {formatCount(likes)}
          </span>
        </div>

        {/* 댓글 */}
        <div className="flex items-center gap-1">
          <Image src="/icons/chat-bubble.svg" width={20} height={20} alt="" />
          <span className="text-sm">
            {formatCount(comments)}
          </span>
        </div>
      </div>
    </article>
  );
}
