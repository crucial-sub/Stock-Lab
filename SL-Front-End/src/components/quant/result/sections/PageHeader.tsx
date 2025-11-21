/**
 * Result 페이지 헤더 섹션
 * - 페이지 제목 및 액션 버튼
 */
import Image from "next/image";
import type { ChangeEvent } from "react";

interface PageHeaderProps {
  onRetryBacktest?: () => void;
  strategyName?: string;
  isEditingName?: boolean;
  editValue?: string;
  isSavingName?: boolean;
  onChangeEditValue?: (value: string) => void;
  onStartEdit?: () => void;
  onSaveEdit?: () => void;
  onCancelEdit?: () => void;
}

export function PageHeader({
  onRetryBacktest,
  strategyName,
  isEditingName = false,
  editValue = "",
  isSavingName = false,
  onChangeEditValue,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
}: PageHeaderProps) {
  return (
    <div className="flex justify-between items-center mb-6">
      <h1 className="flex items-center gap-3 text-[1.75rem] font-semibold text-body">
        {isEditingName ? (
          <>
            <input
              value={editValue}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                onChangeEditValue?.(e.target.value)
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  onSaveEdit?.();
                }
              }}
              className="px-3 py-1.5 min-w-[240px] rounded-sm border border-surface bg-base-0 text-body focus:outline-none focus:border-brand-soft focus:ring-2 focus:ring-brand-soft transition-shadow"
              aria-label="백테스트 이름 입력"
            />
            <button
              type="button"
              onClick={onSaveEdit}
              disabled={isSavingName || !editValue.trim()}
              className="px-3 py-1.5 rounded-sm bg-brand-soft text-brand font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              저장
            </button>
            <button
              type="button"
              onClick={onCancelEdit}
              className="px-3 py-1.5 rounded-sm text-muted hover:text-body transition-colors"
            >
              취소
            </button>
          </>
        ) : (
          <>
            {strategyName ? <span>{strategyName}</span> : null}
            {strategyName && onStartEdit ? (
              <button
                type="button"
                onClick={onStartEdit}
                className="p-1 -m-1 rounded-xs hover:bg-brand-soft transition-colors"
                aria-label="백테스트 이름 수정"
              >
                <Image
                  src="/icons/edit_square.svg"
                  alt=""
                  width={24}
                  height={24}
                  className="object-contain"
                />
              </button>
            ) : null}
          </>
        )}
      </h1>
    </div>
  );
}
