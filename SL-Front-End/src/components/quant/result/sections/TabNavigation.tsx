/**
 * Result 페이지 탭 네비게이션
 * - 매매종목 정보, 수익률, 매매결과, 거래 내역, 설정 조건 탭
 */
type TabType = "stockInfo" | "returns" | "statistics" | "history" | "settings";

interface TabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export function TabNavigation({ activeTab, onTabChange }: TabNavigationProps) {
  const tabs: Array<{ id: TabType; label: string }> = [
    { id: "stockInfo", label: "매매종목 정보" },
    { id: "returns", label: "수익률" },
    { id: "statistics", label: "매매결과" },
    { id: "history", label: "거래 내역" },
    { id: "settings", label: "설정 조건" },
  ];

  return (
    <div className="flex gap-3 mb-6">
      {tabs.map((tab) => (
        <TabButton
          key={tab.id}
          label={tab.label}
          active={activeTab === tab.id}
          onClick={() => onTabChange(tab.id)}
        />
      ))}
    </div>
  );
}

/**
 * 탭 버튼 컴포넌트
 */
function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-6 py-2 rounded-lg font-semibold text-[1.25rem] transition-colors ${active
        ? "bg-brand-purple text-white"
        : "hover:bg-brand-soft"
        }`}
    >
      {label}
    </button>
  );
}