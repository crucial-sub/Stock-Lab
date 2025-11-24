/**
 * Result 페이지 헤더 섹션
 * - 페이지 제목 및 액션 버튼
 */
import Image from "next/image";
import type { ChangeEvent } from "react";

interface PageHeaderProps {
  title?: string;
  subtitle?: string;
  onBack?: () => void;
  onRetryBacktest?: () => void;
  strategyName?: string;
  isEditingName?: boolean;
  editValue?: string;
  isSavingName?: boolean;
  onChangeEditValue?: (value: string) => void;
  onStartEdit?: () => void;
  onSaveEdit?: () => void;
  onCancelEdit?: () => void;
  // 액션 버튼 관련
  isOwner?: boolean;
  isPublic?: boolean;
  onClone?: () => void;
  onToggleShare?: () => void;
}

export function PageHeader({
  onBack,
  onRetryBacktest,
  strategyName,
  isEditingName = false,
  editValue = "",
  isSavingName = false,
  onChangeEditValue,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  isOwner,
  isPublic,
  onClone,
  onToggleShare,
}: PageHeaderProps) {
  return (
    <div className="flex justify-between items-center mb-6">
      {onBack && (
        <button
          onClick={onBack}
          className="text-sm text-gray-500 hover:text-gray-700 mb-1"
        >
          ← 돌아가기
        </button>
      )}
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

      {/* 우측 액션 버튼 */}
      <div className="ml-auto flex gap-2">
        {/* 복제 버튼 */}
        <button
          onClick={onClone}
          className="px-4 py-2 rounded-[12px] bg-brand-purple text-white font-semibold hover:opacity-80 transition-opacity"
        >
          전략 복제
        </button>

        {/* 공유 토글 버튼 */}
        {isOwner && (
          <button
            onClick={onToggleShare}
            className="px-4 py-2 rounded-[12px] bg-brand-purple text-white font-semibold hover:opacity-80 transition-opacity"
          >
            {isPublic ? "전략 공유 해제하기" : "전략 공유하기"}
          </button>
        )}

      </div>
    </div>
  );
}
