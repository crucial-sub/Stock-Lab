"use client";

import { Icon } from "@/components/common/Icon";
import { getTagStyle } from "@/components/community/tagStyles";

export interface FreeBoardPostCardProps {
  tag: string;
  title: string;
  author: string;
  date: string;
  preview: string;
  views: number;
  likes: number;
  comments: number;
  onClick?: () => void;
}

const formatCount = (count: number) => (count > 999 ? "999+" : count.toString());

export function FreeBoardPostCard({
  tag,
  title,
  author,
  date,
  preview,
  views,
  likes,
  comments,
  onClick,
}: FreeBoardPostCardProps) {
  const tagStyle = getTagStyle(tag);
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] p-5 text-left transition hover:shadow-elev-card-soft"
    >
      <div className="flex items-center gap-3 text-[#646464]">
        <span
          className={`rounded-[4px] border px-[10px] pt-0.5 text-[0.75rem] font-normal ${tagStyle.background} ${tagStyle.text} ${tagStyle.border}`}
        >
          {tag}
        </span>
        <span className="text-[0.875rem] text-muted">
          by. {author}, {date}
        </span>
      </div>

      <p className="mt-3 text-[1.25rem] font-semibold text-black">{title}</p>
      <p className="mt-1 text-[1rem] font-semibold text-muted line-clamp-2">{preview}</p>

      <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-[#646464]">
        <Metric icon="/icons/visibility.svg" label={formatCount(views)} />
        <Metric icon="/icons/favorite.svg" label={formatCount(likes)} />
        <Metric icon="/icons/chat-bubble.svg" label={formatCount(comments)} />
      </div>
    </button>
  );
}

function Metric({ icon, label }: { icon: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-sm text-[#646464]">
      <Icon src={icon} alt="stat" size={16} />
      {label}
    </span>
  );
}
