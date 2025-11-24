"use client";

import { useMemo, useState, type FormEvent } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useInfiniteQuery } from "@tanstack/react-query";
import { communityQueryKey, useCloneStrategyMutation } from "@/hooks/useCommunityQuery";
import { strategyApi, type PublicStrategyListItem } from "@/lib/api/strategy";

const PAGE_SIZE = 12;

type FilterValue = "all" | "mine" | "return10to20" | "return20plus";
type SortValue = "returnDesc" | "recent";

const filterTabs: { label: string; value: FilterValue }[] = [
  { label: "전체", value: "all" },
  { label: "내가 공유한 포트폴리오", value: "mine" },
  { label: "수익률 10% ~ 20%", value: "return10to20" },
  { label: "수익률 20% 이상", value: "return20plus" },
];

const sortOptions: { label: string; value: SortValue }[] = [
  { label: "수익률 순으로 보기", value: "returnDesc" },
  { label: "최신순 보기", value: "recent" },
];

const formatDateTime = (date: string) => {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return "-";
  const yyyy = parsed.getFullYear();
  const mm = String(parsed.getMonth() + 1).padStart(2, "0");
  const dd = String(parsed.getDate()).padStart(2, "0");
  const hh = String(parsed.getHours()).padStart(2, "0");
  const min = String(parsed.getMinutes()).padStart(2, "0");
  return `${yyyy}.${mm}.${dd} ${hh}:${min}`;
};

const formatReturnRate = (returnRate: number | null) => {
  if (returnRate === null || typeof returnRate !== "number") return "-";
  const fixed = returnRate.toFixed(2);
  return returnRate > 0 ? `+${fixed}` : fixed;
};

const removeTrailingStrategyWord = (text: string) => {
  return text.replace(/\s*전략(?:입니다)?[.!?]?$/g, "").trim();
};

const buildStrategyConditionText = (item: PublicStrategyListItem) => {
  if (item.hideStrategyDetails) {
    return "상세 조건이 비공개로 설정되어 있습니다.";
  }

  if (!item.description) {
    return "조건 정보가 제공되지 않았습니다.";
  }

  const rawConditions = item.description
    .split(/[\n,.]/)
    .map((cond) => cond.trim())
    .map(removeTrailingStrategyWord)
    .map((cond) => cond.replace(/\s{2,}/g, " ").trim())
    .filter((cond) => cond.length > 1);

  if (!rawConditions.length) {
    return "조건 정보가 제공되지 않았습니다.";
  }

  const maxDisplay = 4;
  const displayed = rawConditions.slice(0, maxDisplay).join(", ");
  const suffix = rawConditions.length > maxDisplay ? ", ..." : "";
  return `${displayed}${suffix}`;
};

export function PublicStrategiesPageClient() {
  const router = useRouter();
  const cloneStrategyMutation = useCloneStrategyMutation();
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterValue>("all");
  const [sortValue, setSortValue] = useState<SortValue>("returnDesc");

  // 전략 복제 핸들러
  const handleCloneStrategy = (sessionId: string, strategyName: string) => {
    if (
      confirm(`"${strategyName}" 전략을 내 포트폴리오에 복제하시겠습니까?`)
    ) {
      cloneStrategyMutation.mutate(sessionId, {
        onSuccess: () => {
          alert("전략이 성공적으로 복제되었습니다.");
        },
        onError: (error) => {
          alert(`복제 실패: ${error.message}`);
        },
      });
    }
  };

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: communityQueryKey.publicStrategies({ limit: PAGE_SIZE }),
    queryFn: ({ pageParam = 1 }) =>
      strategyApi.getPublicStrategies({
        page: pageParam as number,
        limit: PAGE_SIZE,
      }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.hasNext ? pages.length + 1 : undefined,
    initialPageParam: 1,
    staleTime: 1000 * 60 * 5,
  });

  const strategies: PublicStrategyListItem[] =
    data?.pages.flatMap((page) => page.strategies) || [];

  const filteredStrategies = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    let next = strategies.filter((item) => {
      if (!normalizedSearch) return true;
      const combined =
        `${item.strategyName} ${item.ownerName ?? ""} ${item.description ?? ""}`.toLowerCase();
      return combined.includes(normalizedSearch);
    });

    next = next.filter((item) => {
      if (activeFilter === "return10to20") {
        return typeof item.totalReturn === "number" && item.totalReturn >= 10 && item.totalReturn < 20;
      }
      if (activeFilter === "return20plus") {
        return typeof item.totalReturn === "number" && item.totalReturn >= 20;
      }
      if (activeFilter === "mine") {
        // 서버에서 제공하는 별도 플래그가 없어 익명 공개 여부를 사용해 간접 필터링
        return !item.isAnonymous;
      }
      return true;
    });

    return next.sort((a, b) => {
      if (sortValue === "recent") {
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      }
      const aReturn = typeof a.totalReturn === "number" ? a.totalReturn : -Infinity;
      const bReturn = typeof b.totalReturn === "number" ? b.totalReturn : -Infinity;
      return bReturn - aReturn;
    });
  }, [strategies, searchTerm, activeFilter, sortValue]);

  const handleSearchSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
  };

  return (
    <div className="mx-auto max-w-[1000px] pt-[60px]">
      <button
        type="button"
        onClick={() => router.push("/community")}
        className="flex items-center gap-1 text-[0.875rem] font-normal text-muted"
      >
        <Image
          src="/icons/arrow_left.svg"
          alt="뒤로가기"
          width={16}
          height={16}
          color="#C8C8C8"
        />
        돌아가기
      </button>

      <div className="mt-[40px] flex flex-col gap-4">
        <div>
          <p className="text-[1.5rem] font-semibold text-body">공유 포트폴리오</p>
        </div>

        <div className="flex flex-col gap-5 md:flex-row md:items-center">
          <form
            onSubmit={handleSearchSubmit}
            className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center"
          >
            <div className="flex flex-1 items-center rounded-[12px] bg-[#1822340D] border-[0.5px] border-[#18223433] px-[1rem] py-3 shadow-elev-card-soft">
              <input
                type="text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="포트폴리오 이름, 종목명으로 검색"
                className="w-full bg-transparent text-[1rem] text-body placeholder:text-muted focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="flex items-center justify-center gap-1 rounded-[12px] bg-brand-purple px-5 py-3 text-[1rem] font-normal text-white shadow-elev-card-soft transition hover:opacity-80"
            >
              <Image
                src="/icons/search.svg"
                alt="검색"
                width={20}
                height={20}
              />
              검색
            </button>
          </form>

          <select
            value={sortValue}
            onChange={(event) => setSortValue(event.target.value as SortValue)}
            className="rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] px-3 py-3.5 text-[0.875rem] text-muted shadow-elev-card-soft focus:outline-none"
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {filterTabs.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setActiveFilter(tab.value)}
              className={`rounded-full px-4 pt-1.5 pb-1 text-[0.875rem] font-normal transition ${activeFilter === tab.value
                ? "bg-brand-purple text-white font-semibold"
                : "border-[0.5px] border-[#18223433] text-muted"
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-5">
        {isLoading ? (
          <div className="py-20 text-center text-muted font-semibold">로딩 중...</div>
        ) : error ? (
          <div className="py-20 text-center text-muted font-semibold">
            공개 포트폴리오 데이터를 불러올 수 없습니다.
          </div>
        ) : filteredStrategies.length === 0 ? (
          <div className="py-20 text-center text-muted font-semibold">
            조건에 맞는 포트폴리오가 없습니다.
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-5">
              {filteredStrategies.map((item) => {
                const formattedReturn = formatReturnRate(item.totalReturn);
                const isPositive =
                  typeof item.totalReturn === "number" && item.totalReturn >= 0;
                const holdingMessage = buildStrategyConditionText(item);

                return (
                  <article
                    key={item.strategyId}
                    className="flex flex-col gap-5 rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] p-5 shadow-elev-card-soft hover:bg-white/20 md:flex-row md:items-center"
                  >
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          onClick={() => {
                            if (item.sessionId) {
                              router.push(`/quant/result/${item.sessionId}`);
                            }
                          }}
                          className="text-[1.25rem] font-semibold text-black hover:text-brand-purple transition-colors cursor-pointer text-left"
                        >
                          {item.strategyName}
                        </button>
                        <span className="text-[0.75rem] text-muted">
                          by. {item.ownerName || (item.isAnonymous ? "익명" : "알 수 없음")},
                        </span>
                        <span className="text-[0.75rem] text-muted">
                          {formatDateTime(item.updatedAt || item.createdAt)}
                        </span>
                      </div>
                      <div>
                        <p className="mt-3 text-[1rem] font-normal text-muted">
                          설정 조건
                        </p>
                        <span className="text-[0.875rem] font-normal text-muted">
                          {holdingMessage}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-4 md:w-[220px]">
                      <div className="text-right">
                        <p
                          className={`text-[1.5rem] font-bold ${isPositive ? "text-price-up" : "text-price-down"
                            }`}
                        >
                          {formattedReturn}
                          {formattedReturn !== "-" && <span className="text-base">%</span>}
                        </p>
                        <p className="text-[0.875rem] font-normal text-muted">누적 수익률</p>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>

            {hasNextPage && (
              <div className="flex justify-center pt-8">
                <button
                  type="button"
                  onClick={() => fetchNextPage()}
                  disabled={isFetchingNextPage}
                  className="rounded-full border border-transparent bg-white/80 px-8 py-3 text-sm font-semibold text-[#4b2fd6] shadow-[0_20px_50px_rgba(75,47,214,0.15)] transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isFetchingNextPage ? "불러오는 중..." : "더 보기"}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
