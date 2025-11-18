"use client";

import { useState } from "react";

const TAG_OPTIONS = ["질문", "토론", "정보 공유"];

export interface FreeBoardPostFormValues {
  title: string;
  content: string;
  tag?: string;
}

interface FreeBoardPostFormProps {
  isSubmitting?: boolean;
  onSubmit: (values: FreeBoardPostFormValues) => void;
}

export function FreeBoardPostForm({
  isSubmitting = false,
  onSubmit,
}: FreeBoardPostFormProps) {
  const [values, setValues] = useState<FreeBoardPostFormValues>({
    title: "",
    content: "",
    tag: TAG_OPTIONS[0],
  });

  const handleChange = (field: keyof FreeBoardPostFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    if (!values.title.trim() || !values.content.trim()) return;
    onSubmit({
      title: values.title.trim(),
      content: values.content.trim(),
      tag: values.tag,
    });
  };

  return (
    <div className="rounded-[12px] border border-[#18223414] bg-[#1822340D] p-6">
      <div className="flex flex-wrap items-center gap-2 text-sm text-[#646464]">
        <span className="font-semibold">태그:</span>
        {TAG_OPTIONS.map((tag) => {
          const selected = values.tag === tag;
          return (
            <button
              key={tag}
              type="button"
              onClick={() => handleChange("tag", tag)}
              className={`rounded-[4px] px-3 py-1 text-xs font-semibold ${
                selected
                  ? "bg-brand-purple text-white"
                  : "bg-white/60 text-[#646464]"
              }`}
            >
              {tag}
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex flex-col gap-3">
        <input
          type="text"
          value={values.title}
          onChange={(e) => handleChange("title", e.target.value)}
          placeholder="제목을 작성하세요."
          className="rounded-[12px] border border-[#18223414] bg-white px-4 py-3 text-sm text-black placeholder:text-[#AC64FF80] focus:border-brand-purple focus:outline-none"
        />
        <textarea
          value={values.content}
          onChange={(e) => handleChange("content", e.target.value)}
          placeholder="본문을 작성하세요."
          className="min-h-[200px] rounded-[12px] border border-[#18223414] bg-white px-4 py-3 text-sm text-black placeholder:text-[#AC64FF80] focus:border-brand-purple focus:outline-none"
        />
      </div>

      <div className="mt-4 flex justify-end">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className={`rounded-[12px] px-6 py-2 text-sm font-semibold text-white transition ${
            isSubmitting ? "bg-[#AC64FF80]" : "bg-brand-purple hover:bg-brand-purple/90"
          }`}
        >
          {isSubmitting ? "게시 중..." : "게시하기"}
        </button>
      </div>
    </div>
  );
}
