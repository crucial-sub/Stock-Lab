import Image from "next/image";

/**
 * 체크박스 그룹 공통 컴포넌트
 * - 여러 체크박스 항목을 그리드 레이아웃으로 표시
 * - 전체 선택 기능 포함
 */
interface CheckboxItem {
  id: string;
  label: string;
}

interface CheckboxGroupProps {
  title: string;
  items: CheckboxItem[];
  selectedIds: Set<string>;
  onToggleItem: (id: string) => void;
  onToggleAll: () => void;
  isAllSelected?: boolean; // 외부에서 전달받을 수 있도록 추가
  columns?: 2 | 3 | 4 | 5 | 6;
  className?: string;
}

export function CheckboxGroup({
  title,
  items,
  selectedIds,
  onToggleItem,
  onToggleAll,
  isAllSelected: isAllSelectedProp,
  columns = 6,
  className = "",
}: CheckboxGroupProps) {
  // prop이 전달되면 사용하고, 아니면 내부에서 계산
  const isAllSelected =
    isAllSelectedProp !== undefined
      ? isAllSelectedProp
      : items.length > 0 && items.every((item) => selectedIds.has(item.id));

  const gridColsClass = {
    2: "grid-cols-2",
    3: "grid-cols-3",
    4: "grid-cols-4",
    5: "grid-cols-5",
    6: "grid-cols-6",
  }[columns];

  return (
    <div className={className}>
      <div className="flex items-center gap-3 mb-3">
        <h4 className="text-base font-semibold text-text-strong">{title}</h4>
        <button
          type="button"
          onClick={onToggleAll}
          className="flex items-center gap-2"
        >
          <div
            className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
              isAllSelected
                ? "bg-accent-primary border-accent-primary"
                : "border-border-default"
            }`}
          >
            {isAllSelected && (
              <Image src="/icons/check_box.svg" alt="" width={16} height={16} />
            )}
          </div>
          <span className="text-sm text-accent-primary">전체선택</span>
        </button>
      </div>

      <div className={`grid ${gridColsClass} gap-3`}>
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onToggleItem(item.id)}
            className="flex items-center gap-2"
          >
            <div
              className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                selectedIds.has(item.id)
                  ? "bg-accent-primary border-accent-primary"
                  : "border-border-default"
              }`}
            >
              {selectedIds.has(item.id) && (
                <Image
                  src="/icons/check_box.svg"
                  alt=""
                  width={16}
                  height={16}
                />
              )}
            </div>
            <span className="text-sm text-text-body">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
