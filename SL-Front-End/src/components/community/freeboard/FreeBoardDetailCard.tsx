"use client";

import { Icon } from "@/components/common/Icon";
import { getTagStyle } from "@/components/community/tagStyles";

interface FreeBoardDetailCardProps {
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
}

const formatCount = (count: number) => (count > 999 ? "999+" : count.toString());

export function FreeBoardDetailCard({
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
}: FreeBoardDetailCardProps) {
  const tagStyle = getTagStyle(tag);
  return (
    <div className="w-full rounded-[12px] border border-[#18223414] bg-[#1822340D] p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <span
            className={`inline-flex items-center rounded-[4px] border px-[10px] pt-0.5 text-[0.75rem] font-normal ${tagStyle.background} ${tagStyle.text} ${tagStyle.border}`}
          >
            {tag}
          </span>
          <h1 className="mt-2 text-2xl font-semibold text-black">{title}</h1>
          <p className="mt-1 text-sm text-[#646464]">
            by. {author} · {date}
          </p>
        </div>
        <button
          type="button"
        onClick={onLike}
        className={`flex h-10 w-10 items-center justify-center rounded-full border ${
            isLiked ? "border-[#ef4444] bg-[#FFF1F2]" : "border-[#18223414] bg-white"
          } transition`}
        aria-label="공감"
      >
        <Icon
          src="/icons/favorite.svg"
          alt="favorite"
          size={20}
          color={isLiked ? "#ef4444" : undefined}
        />
      </button>
      </div>

      <div className="mt-4 whitespace-pre-line text-base leading-relaxed text-[#000000]">
        {content}
      </div>

      <div className="mt-6 flex items-center gap-5 text-sm text-[#646464]">
        <Metric icon="/icons/visibility.svg" label={formatCount(views)} />
        <Metric
          icon="/icons/favorite.svg"
          label={formatCount(likes)}
          color={isLiked ? "#ef4444" : undefined}
        />
        <Metric icon="/icons/chat-bubble.svg" label={formatCount(comments)} />
      </div>
    </div>
  );
}

function Metric({
  icon,
  label,
  color,
}: {
  icon: string;
  label: string;
  color?: string;
}) {
  return (
    <span className="inline-flex items-center gap-1 text-sm text-[#646464]">
      <Icon src={icon} alt="stat" size={18} color={color} />
      {label}
    </span>
  );
}
