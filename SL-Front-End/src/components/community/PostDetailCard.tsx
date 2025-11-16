import Image from "next/image";

export interface PostDetailCardProps {
  tag: string;
  title: string;
  author: string;
  date: string;
  content: string;
  views: number;
  likes: number;
  comments: number;
  isLiked?: boolean;
  onLike?: () => void;
  className?: string;
}

/**
 * 게시글 상세 카드 컴포넌트
 * - 게시글의 전체 내용 표시
 * - 좋아요 기능 포함
 */
export function PostDetailCard({
  tag,
  title,
  author,
  date,
  content,
  views,
  likes,
  comments,
  isLiked = false,
  onLike,
  className = "",
}: PostDetailCardProps) {
  const formatCount = (count: number): string => {
    return count > 999 ? "999+" : count.toString();
  };

  return (
    <article
      className={`flex flex-col w-full rounded-lg border border-surface px-5 py-5 ${className}`}
    >
      {/* 태그 */}
      <div className="mb-5">
        <span className="px-3 py-1 text-xs font-medium text-blue-500 bg-[#EAF5FF] border border-blue-500 rounded">
          {tag}
        </span>
      </div>

      {/* 제목 */}
      <h1 className="text-[28px] font-semibold text-body mb-4">
        {title}
      </h1>

      {/* 작성자 및 날짜 */}
      <div className="flex items-center gap-2 text-base text-muted mb-6">
        <span>by. {author}</span>
        <span>{date}</span>
      </div>

      {/* 구분선 */}
      <div className="w-full h-[0.5px] bg-surface mb-6" />

      {/* 본문 내용 */}
      <p className="text-2xl text-body mb-6">
        {content}
      </p>

      {/* 구분선 */}
      <div className="w-full h-[0.5px] bg-surface mb-6" />

      {/* 통계 정보 */}
      <div className="flex items-center justify-end gap-5 mb-6">
        <div className="flex items-center gap-1">
          <Image src="/icons/visibility.svg" width={20} height={20} alt="" />
          <span className="text-sm text-body">
            {formatCount(views)}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <Image src="/icons/favorite.svg" width={20} height={20} alt="" />
          <span className="text-sm text-price-up">
            {formatCount(likes)}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <Image src="/icons/chat-bubble.svg" width={20} height={20} alt="" />
          <span className="text-sm text-body">
            {formatCount(comments)}
          </span>
        </div>
      </div>

      {/* 좋아요 버튼 */}
      <button
        onClick={onLike}
        className={`inline-flex items-center gap-2 px-6 py-2 rounded-lg border self-start ${
          isLiked
            ? "bg-[#FFF6F6] border-price-up text-price-up"
            : "bg-transparent border-price-up text-price-up"
        }`}
      >
        <Image
          src="/icons/favorite.svg"
          width={24}
          height={24}
          alt=""
          className={isLiked ? "opacity-100" : "opacity-70"}
        />
        <span className="text-xl font-semibold">좋아요</span>
      </button>
    </article>
  );
}
