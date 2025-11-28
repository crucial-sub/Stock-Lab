const TAG_STYLE_MAP: Record<
  string,
  { background: string; text: string; border: string }
> = {
  질문: {
    background: "bg-[#E9F1FF]",
    text: "text-[#1D4ED8]",
    border: "border-[#93C5FD]",
  },
  토론: {
    background: "bg-[#FFF5E6]",
    text: "text-[#EA580C]",
    border: "border-[#FECBA1]",
  },
  "정보 공유": {
    background: "bg-[#ECFDF3]",
    text: "text-[#15803D]",
    border: "border-[#BBF7D0]",
  },
};

const DEFAULT_TAG_STYLE = {
  background: "bg-[#F4F4F5]",
  text: "text-[#52525B]",
  border: "border-[#E4E4E7]",
};

export function getTagStyle(tag: string | undefined) {
  if (!tag) {
    return DEFAULT_TAG_STYLE;
  }
  return TAG_STYLE_MAP[tag] ?? DEFAULT_TAG_STYLE;
}
