import Image from "next/image";

/**
 * 사이드바 네비게이션 아이템 컴포넌트
 *
 * @description 홈 화면 사이드바의 개별 메뉴 아이템입니다.
 * 활성 상태에 따라 다른 스타일이 적용됩니다.
 *
 * @example
 * ```tsx
 * <NavItem
 *   icon="/icons/home.svg"
 *   label="홈"
 *   isActive={true}
 *   onClick={() => router.push("/home")}
 * />
 * ```
 */

interface NavItemProps {
  /** 아이콘 경로 (public/icons/에서 상대 경로) */
  icon: string;
  /** 메뉴 레이블 텍스트 */
  label: string;
  /** 활성 상태 여부 */
  isActive?: boolean;
  /** 클릭 이벤트 핸들러 */
  onClick?: () => void;
}

export function NavItem({
  icon,
  label,
  isActive = false,
  onClick,
}: NavItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "flex items-center gap-3 px-4 py-3 rounded-lg",
        "w-full h-14 shrink-0",
        "transition-all duration-200",
        isActive
          ? "bg-sidebar-item-active text-sidebar-item-active border border-sidebar-item-active"
          : "text-sidebar-item hover:bg-sidebar-item-sub-active",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-current={isActive ? "page" : undefined}
    >
      <div className="relative w-5 h-5">
        <Image
          src={icon}
          alt=""
          fill
          className="object-contain"
          aria-hidden="true"
        />
      </div>
      <span className="text-xl font-semibold">{label}</span>
    </button>
  );
}
