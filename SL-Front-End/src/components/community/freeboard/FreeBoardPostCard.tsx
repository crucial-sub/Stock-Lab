"use client";

import { Icon } from "@/components/common/Icon";

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
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-[12px] border border-[#18223414] bg-[#1822340D] p-5 text-left transition hover:border-brand-purple hover:shadow-[0_4px_20px_rgba(0,0,0,0.08)]"
    >
      <div className="flex items-center gap-2 text-sm text-[#646464]">
        <span className="rounded-[4px] bg-white/40 px-2 py-0.5 text-xs font-semibold text-[#646464]">
          {tag}
        </span>
        <span className="text-sm text-[#646464]">
          by. {author} · {date}
        </span>
      </div>

      <p className="mt-2 text-lg font-semibold text-black">{title}</p>
      <p className="mt-1 text-sm text-[#646464] line-clamp-2">{preview}</p>

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
