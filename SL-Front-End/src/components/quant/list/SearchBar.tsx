import Image from "next/image";

/**
 * 전략 검색바 컴포넌트
 * - 전략 이름으로 검색 기능
 */
interface SearchBarProps {
  /** 검색 키워드 */
  value: string;
  /** 검색 키워드 변경 핸들러 */
  onChange: (value: string) => void;
  /** 검색 실행 핸들러 (Enter 키 또는 검색 아이콘 클릭 시) */
  onSearch?: () => void;
  /** placeholder 텍스트 */
  placeholder?: string;
}

export function SearchBar({
  value,
  onChange,
  onSearch,
  placeholder = "전략 이름으로 검색하기",
}: SearchBarProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && onSearch) {
      onSearch();
    }
  };

  return (
    <div className="flex h-10 relative gap-3">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-60 rounded-md border border-tag-neutral p-3 font-normal text-[12px]"
      />
      <div className="flex w-10 rounded-md p-2 gap-5 justify-center items-center bg-[#f0f0f0]">
        <Image
          src="/icons/search_icon.svg"
          alt="검색"
          width={24}
          height={24}
          onClick={onSearch}
        />
      </div>
    </div>
  );
}
