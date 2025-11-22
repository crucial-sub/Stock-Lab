"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { CreatePortfolioCard } from "@/components/quant/CreatePortfolioCard";
import { PortfolioCard } from "@/components/quant/PortfolioCard";
import { PortfolioDashboard } from "@/components/quant/PortfolioDashboard";
import { PortfolioShareModal } from "@/components/modal/PortfolioShareModal";
import { strategyApi } from "@/lib/api/strategy";

/**
 * 포트폴리오 페이지 클라이언트 컴포넌트
 *
 * @description 포트폴리오 목록과 대시보드를 표시하는 클라이언트 컴포넌트
 * 인터랙션과 상태 관리를 담당합니다.
 */

interface Portfolio {
  id: string;
  strategyId: string;
  title: string;
  profitRate: number;
  isActive: boolean;
  status: string;
  sourceSessionId?: string | null;
  lastModified: string;
  createdAt: string;
}

interface PortfolioPageClientProps {
  /** 총 모의 자산 */
  totalAssets: number;
  /** 평가손익 */
  totalProfit: number;
  /** 수익률 */
  totalReturn: number;
  /** 평가금액 */
  evaluationAmount: number;
  /** 활성 포트폴리오 개수 */
  activePortfolioCount: number;
  /** 포트폴리오 목록 */
  portfolios: Portfolio[];
}

export function PortfolioPageClient({
  totalAssets,
  totalProfit,
  totalReturn,
  evaluationAmount,
  activePortfolioCount,
  portfolios: initialPortfolios,
}: PortfolioPageClientProps) {
  const router = useRouter();

  // 포트폴리오 목록 상태 (삭제 후 UI 업데이트를 위해)
  const [portfolios, setPortfolios] = useState<Portfolio[]>(initialPortfolios);

  // 선택된 포트폴리오 ID 목록
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // 삭제 진행 중 상태
  const [isDeleting, setIsDeleting] = useState(false);

  // 공유 모달 상태
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareTarget, setShareTarget] = useState<
    Pick<Portfolio, "id" | "strategyId" | "title"> | null
  >(null);
  // 이름 수정 상태
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState<string>("");
  const [isRenaming, setIsRenaming] = useState(false);

  // 포트폴리오 선택/해제 핸들러
  const handleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // 포트폴리오 클릭 핸들러 - 상태에 따라 다른 페이지로 이동
  const handlePortfolioClick = (id: string) => {
    const portfolio = portfolios.find((p) => p.id === id);
    if (!portfolio) return;

    // 자동매매 전략 카드인 경우 자동매매 상태 페이지로 이동
    if (id.startsWith("auto-")) {
      if (portfolio.strategyId) {
        router.push(`/quant/auto-trading/${portfolio.strategyId}`);
      }
      return;
    }

    // PENDING 상태 - 백테스트 설정 화면으로 이동
    if (portfolio.status === "PENDING") {
      if (portfolio.sourceSessionId) {
        // 복제된 전략 - 조건 자동 채움
        router.push(`/quant/new?clone=${portfolio.sourceSessionId}`);
      } else {
        // 새로 만든 전략 - 빈 화면 (현재는 사용 안함)
        router.push(`/quant/new`);
      }
      return;
    }

    // RUNNING, COMPLETED 등 - 결과 화면으로 이동
    router.push(`/quant/result/${id}`);
  };

  // 선택 항목 삭제 핸들러
  const handleDeleteSelected = async () => {
    // 선택된 항목이 없으면 종료
    if (selectedIds.size === 0) {
      alert("삭제할 포트폴리오를 선택해주세요.");
      return;
    }

    // 사용자 확인
    const confirmed = window.confirm(
      `선택한 ${selectedIds.size}개의 포트폴리오를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsDeleting(true);

      // API 호출 - 선택된 ID 배열로 변환
      const sessionIds = Array.from(selectedIds);
      await strategyApi.deleteBacktestSessions(sessionIds);

      // 성공: 로컬 상태에서 삭제된 항목 제거
      setPortfolios((prev) =>
        prev.filter((portfolio) => !selectedIds.has(portfolio.id)),
      );

      // 선택 상태 초기화
      setSelectedIds(new Set());

      // 성공 메시지
      alert(`${sessionIds.length}개의 포트폴리오가 삭제되었습니다.`);

      // 페이지 새로고침 (대시보드 통계 업데이트를 위해)
      router.refresh();
    } catch (error: unknown) {
      console.error("포트폴리오 삭제 실패:", error);

      // 에러 메시지 표시
      const errorMessage =
        (
          error as {
            response?: { data?: { detail?: string } };
            message?: string;
          }
        )?.response?.data?.detail ||
        (error as { message?: string })?.message ||
        "포트폴리오 삭제 중 오류가 발생했습니다.";
      alert(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  // 공유 모달 오픈
  const handleOpenShare = (
    portfolio: Pick<Portfolio, "id" | "strategyId" | "title">,
  ) => {
    if (!portfolio.strategyId) {
      alert("공유할 전략 정보를 찾을 수 없습니다.");
      return;
    }
    setShareTarget(portfolio);
    setIsShareModalOpen(true);
  };

  // 공유 설정 저장
  const handleShareConfirm = async ({
    description,
    isAnonymous,
  }: {
    description: string;
    isAnonymous: boolean;
  }) => {
    if (!shareTarget?.strategyId) {
      throw new Error("공유할 전략 정보를 찾을 수 없습니다.");
    }

    try {
      await Promise.all([
        strategyApi.updateStrategy(shareTarget.strategyId, { description }),
        strategyApi.updateSharingSettings(shareTarget.strategyId, {
          isPublic: true,
          isAnonymous,
        }),
      ]);

      alert("포트폴리오가 공유 설정되었습니다.");
      setIsShareModalOpen(false);
      setShareTarget(null);
    } catch (error: unknown) {
      console.error("포트폴리오 공유 설정 실패:", error);
      const errorMessage =
        (
          error as {
            response?: { data?: { detail?: string } };
            message?: string;
          }
        )?.response?.data?.detail ||
        (error as { message?: string })?.message ||
        "공유 설정에 실패했습니다. 잠시 후 다시 시도해주세요.";
      throw new Error(errorMessage);
    }
  };

  // 전략 이름 수정
  // 이름 수정 시작
  const handleStartRename = (
    portfolio: Pick<Portfolio, "id" | "strategyId" | "title">,
  ) => {
    setEditingId(portfolio.id);
    setEditingValue(portfolio.title);
  };

  // 이름 수정 취소
  const handleCancelRename = () => {
    setEditingId(null);
    setEditingValue("");
  };

  // 이름 수정 저장
  const handleRenameSubmit = async () => {
    if (!editingId) return;
    const portfolio = portfolios.find((p) => p.id === editingId);
    if (!portfolio) return;

    const trimmedName = editingValue.trim();
    if (!trimmedName) {
      alert("전략 이름을 입력해주세요.");
      return;
    }
    if (trimmedName === portfolio.title) {
      handleCancelRename();
      return;
    }

    try {
      setIsRenaming(true);
      await strategyApi.updateStrategy(portfolio.strategyId, {
        strategyName: trimmedName,
      });

      setPortfolios((prev) =>
        prev.map((item) =>
          item.id === portfolio.id ? { ...item, title: trimmedName } : item,
        ),
      );
      handleCancelRename();
    } catch (error: unknown) {
      console.error("전략 이름 수정 실패:", error);
      const errorMessage =
        (
          error as {
            response?: { data?: { detail?: string } };
            message?: string;
          }
        )?.response?.data?.detail ||
        (error as { message?: string })?.message ||
        "전략 이름 수정 중 문제가 발생했습니다.";
      alert(errorMessage);
    } finally {
      setIsRenaming(false);
    }
  };

  // 활성 포트폴리오를 맨 앞으로, 나머지는 최신순으로 정렬
  const sortedPortfolios = [...portfolios].sort((a, b) => {
    // 1. 활성 상태 우선
    if (a.isActive && !b.isActive) return -1;
    if (!a.isActive && b.isActive) return 1;
    // 2. 같은 활성 상태면 최신순 (createdAt 기준)
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });

  return (
    <main className="flex-1 px-[18.75rem] py-[3.75rem] overflow-auto">
      {/* 대시보드 */}
      <PortfolioDashboard
        totalAssets={totalAssets}
        totalProfit={totalProfit}
        totalReturn={totalReturn}
        evaluationAmount={evaluationAmount}
        activePortfolioCount={activePortfolioCount}
      />
      {/* 제거된 커뮤니티 섹션 (랭킹/공유)는 커뮤니티 페이지로 이동 */}
      {/* 내 포트폴리오 섹션 */}
      <section aria-label="내 포트폴리오">
        {/* 섹션 헤더 */}
        <div className="flex items-center justify-between mb-[40px]">
          <h2 className="text-[2rem] font-bold text-black">내 포트폴리오</h2>
          <button
            type="button"
            onClick={handleDeleteSelected}
            disabled={isDeleting || selectedIds.size === 0}
            className="text-[#c8c8c8] hover:text-black transition-colors underline disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? "삭제 중..." : "선택항목 삭제"}
          </button>
        </div>

        {/* 포트폴리오 그리드 */}
        <div className="grid grid-cols-3 gap-[20px]">
          {/* 새로 만들기 카드 */}
          <CreatePortfolioCard />

          {/* 모든 포트폴리오 (활성 우선, 최신순) */}
          {sortedPortfolios.map((portfolio) => (
            <PortfolioCard
              key={portfolio.id}
              {...portfolio}
              isSelected={selectedIds.has(portfolio.id)}
              onSelect={handleSelect}
              onClick={handlePortfolioClick}
              onShare={handleOpenShare}
              onRename={handleStartRename}
              isEditing={editingId === portfolio.id}
              editValue={editingId === portfolio.id ? editingValue : undefined}
              onEditChange={setEditingValue}
              onEditSubmit={handleRenameSubmit}
              onEditCancel={handleCancelRename}
              isRenaming={isRenaming}
            />
          ))}
        </div>
      </section>

      <PortfolioShareModal
        isOpen={isShareModalOpen}
        portfolioName={shareTarget?.title}
        onClose={() => {
          setIsShareModalOpen(false);
          setShareTarget(null);
        }}
        onConfirm={handleShareConfirm}
      />
    </main>
  );
}
