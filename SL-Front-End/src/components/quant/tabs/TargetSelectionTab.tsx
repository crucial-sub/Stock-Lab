"use client";

/**
 * 매매 대상 선택 탭 - DB 연동 버전
 *
 * 개선 사항:
 * - 실제 DB의 industry 컬럼에서 데이터 로드
 * - API 연동으로 실제 종목 데이터 표시
 * - 커스텀 훅으로 비즈니스 로직 분리
 */

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Title } from "@/components/common";
import {
  StockCount,
  TradeTargetHeader,
  UniverseThemeSelection,
} from "@/components/quant/sections";
import { useTradeTargetSelection } from "@/hooks/quant";
import { runBacktest } from "@/lib/api/backtest";
import {
  getIndustries,
  type StockInfo,
  searchStocks,
} from "@/lib/api/industries";
import { getUniversesSummary, getUniverseStockCount } from "@/lib/api/universes";
import type { UniverseInfo } from "@/types/universe";
import { useBacktestConfigStore } from "@/stores";
import { FieldPanel } from "../ui";
import { authApi } from "@/lib/api/auth";

export default function TargetSelectionTab() {
  const { getBacktestRequest } = useBacktestConfigStore();
  const router = useRouter();

  // 유니버스 데이터 상태
  const [universes, setUniverses] = useState<UniverseInfo[]>([]);
  const [selectedUniverses, setSelectedUniverses] = useState<Set<string>>(
    new Set()
  );

  // 산업 데이터 상태 (DB에서 가져옴)
  const [industries, setIndustries] = useState<string[]>([]);
  const [industryStockCounts, setIndustryStockCounts] = useState<
    Map<string, number>
  >(new Map());
  const [isLoadingIndustries, setIsLoadingIndustries] = useState(true);
  const [totalStockCount, setTotalStockCount] = useState(0);

  // 유니버스 기반 종목 수 (동적 계산)
  const [universeBasedStockCount, setUniverseBasedStockCount] = useState(0);
  const [universeTotalStockCount, setUniverseTotalStockCount] = useState(0);

  // 종목 검색 및 선택 상태
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<StockInfo[]>([]);
  const [selectedStocks, setSelectedStocks] = useState<Set<string>>(new Set());
  const [isSearching, setIsSearching] = useState(false);

  // 백테스트 실행 상태
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strategyName, setStrategyName] = useState("");
  const [nickname, setNickname] = useState("사용자");

  // 기본 전략명: 닉네임-YYYYMMDD-HHMMSS (백엔드와 동일 포맷)
  const defaultStrategyName = useMemo(() => {
    const prefix = nickname || "사용자";
    const ts = new Date();
    const pad = (n: number) => n.toString().padStart(2, "0");
    const timestamp = `${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}-${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}`;
    return `${prefix}-${timestamp}`;
  }, [nickname]);

  // 닉네임 불러오기 (기본값 접두어)
  useEffect(() => {
    const loadNickname = async () => {
      try {
        const user = await authApi.getCurrentUser();
        if (user?.nickname) {
          setNickname(user.nickname);
        }
      } catch (err) {
        console.warn("닉네임 조회 실패, 기본값 사용:", err);
      }
    };
    loadNickname();
  }, []);

  // 유니버스 데이터 가져오기
  useEffect(() => {
    async function fetchUniverses() {
      try {
        const data = await getUniversesSummary();
        setUniverses(data.universes);

        // 기본적으로 모든 유니버스 선택
        const allUniverseIds = new Set(data.universes.map((u) => u.id));
        setSelectedUniverses(allUniverseIds);

        // 전체 유니버스의 종목 수 가져오기 (전체 카운트용)
        try {
          const totalResponse = await getUniverseStockCount(Array.from(allUniverseIds));
          setUniverseTotalStockCount(totalResponse.stockCount);
          console.log("🔢 전체 유니버스 종목 수:", totalResponse.stockCount);
        } catch (err) {
          console.error("전체 유니버스 종목 수 조회 실패:", err);
        }

        console.log("=== 유니버스 데이터 로드 성공 ===");
        console.log("유니버스 수:", data.universes.length);
        console.log("기본 선택된 유니버스:", allUniverseIds.size);
        console.log("========================");
      } catch (err) {
        console.error("유니버스 데이터 로드 실패:", err);
      }
    }

    fetchUniverses();
  }, []);

  // DB에서 산업 목록 가져오기
  useEffect(() => {
    async function fetchIndustries() {
      try {
        setIsLoadingIndustries(true);
        const data = await getIndustries();

        // 산업명만 추출
        const industryNames = data.map((item) => item.industry_name);
        setIndustries(industryNames);

        // 산업별 종목 수를 Map으로 캐시
        const countsMap = new Map<string, number>();
        data.forEach((item) => {
          countsMap.set(item.industry_name, item.stock_count);
        });
        setIndustryStockCounts(countsMap);

        // 전체 종목 수 계산
        const total = data.reduce((sum, item) => sum + item.stock_count, 0);
        setTotalStockCount(total);

        console.log("=== 산업 데이터 로드 성공 ===");
        console.log("산업 수:", industryNames.length);
        console.log("전체 종목 수:", total);
        console.log("========================");
      } catch (err) {
        console.error("산업 데이터 로드 실패:", err);
        setError("산업 데이터를 불러오는데 실패했습니다.");
      } finally {
        setIsLoadingIndustries(false);
      }
    }

    fetchIndustries();
  }, []);

  // 선택된 산업의 종목 수 계산
  const [selectedIndustryStockCount, setSelectedIndustryStockCount] =
    useState(0);

  // 최종 선택된 종목 수 계산
  // 1. 유니버스가 선택되어 있고 유효한 종목 수가 있으면 유니버스 기반 사용
  // 2. 유니버스가 선택되어 있지만 종목 수가 0이면 산업 기반으로 폴백
  // 3. 유니버스가 없으면 산업 기반 종목 수 사용
  // 4. 개별 선택 종목 추가
  const finalSelectedCount =
    selectedUniverses.size > 0 && universeBasedStockCount > 0
      ? universeBasedStockCount + selectedStocks.size
      : selectedIndustryStockCount + selectedStocks.size;

  // 최종 전체 종목 수 계산
  // 유니버스가 선택되어 있고 유효한 값이 있으면 유니버스 전체 수 사용
  // 그렇지 않으면 산업 기반 전체 수 사용
  const finalTotalCount =
    selectedUniverses.size > 0 && universeTotalStockCount > 0
      ? universeTotalStockCount
      : totalStockCount;

  // 커스텀 훅으로 매매 대상 선택 로직 관리
  const {
    selectedIndustries,
    isAllIndustriesSelected,
    toggleIndustry,
    toggleAllIndustries,
  } = useTradeTargetSelection(
    industries,
    [],
    Array.from(selectedStocks),
    finalSelectedCount, // 유니버스 또는 산업 기반 종목 수
    finalTotalCount,    // 유니버스 또는 산업 기반 전체 수
  );

  // 유니버스 선택 변경 시 스토어 업데이트 및 종목 수 계산
  const { trade_targets, setTradeTargets } = useBacktestConfigStore();
  useEffect(() => {
    setTradeTargets({
      ...trade_targets,
      selected_universes: Array.from(selectedUniverses),
    });
  }, [selectedUniverses]);

  // 선택된 유니버스의 종목 수 계산
  useEffect(() => {
    async function fetchUniverseStockCount() {
      if (selectedUniverses.size === 0) {
        setUniverseBasedStockCount(0);
        setUniverseTotalStockCount(0);
        // 유니버스가 없을 때는 스토어도 업데이트
        setTradeTargets((prev) => ({
          ...prev,
          total_stock_count: totalStockCount,
        }));
        return;
      }

      try {
        const response = await getUniverseStockCount(
          Array.from(selectedUniverses)
        );
        setUniverseBasedStockCount(response.stockCount);
        setUniverseTotalStockCount(response.stockCount);
        console.log("🔢 유니버스 기반 종목 수:", response.stockCount);

        // 유니버스 종목 수를 스토어에 직접 업데이트
        setTradeTargets((prev) => ({
          ...prev,
          total_stock_count: response.stockCount,
          selected_stock_count: response.stockCount,
        }));
      } catch (err) {
        console.error("유니버스 종목 수 조회 실패:", err);
        setUniverseBasedStockCount(0);
        setUniverseTotalStockCount(0);
      }
    }

    fetchUniverseStockCount();
  }, [selectedUniverses, setTradeTargets, totalStockCount]);

  // 종목 검색 핸들러
  const handleSearch = async (query: string) => {
    setSearchQuery(query);

    if (!query || query.trim() === "") {
      setSearchResults([]);
      return;
    }

    try {
      setIsSearching(true);
      const results = await searchStocks(query);
      setSearchResults(results);
    } catch (err) {
      console.error("종목 검색 실패:", err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // 유니버스 선택/해제 토글
  const toggleUniverse = (universeId: string) => {
    const newSelected = new Set(selectedUniverses);
    if (newSelected.has(universeId)) {
      newSelected.delete(universeId);
    } else {
      newSelected.add(universeId);
    }
    setSelectedUniverses(newSelected);
  };

  // 유니버스 전체선택 여부
  const isAllUniversesSelected =
    universes.length > 0 && selectedUniverses.size === universes.length;

  // 유니버스 전체선택/해제 토글
  const toggleAllUniverses = () => {
    if (isAllUniversesSelected) {
      // 전체 해제
      setSelectedUniverses(new Set());
    } else {
      // 전체 선택
      const allUniverseIds = new Set(universes.map((u) => u.id));
      setSelectedUniverses(allUniverseIds);
    }
  };

  // 종목 선택/해제 토글
  const toggleStockSelection = (stockCode: string) => {
    const newSelected = new Set(selectedStocks);
    if (newSelected.has(stockCode)) {
      newSelected.delete(stockCode);
    } else {
      newSelected.add(stockCode);
    }
    setSelectedStocks(newSelected);
  };

  // 선택된 산업의 종목 수 계산 (캐시된 데이터 사용 - API 호출 없음)
  useEffect(() => {
    // 아무 산업도 선택되지 않았거나 industries가 아직 로드되지 않은 경우
    if (selectedIndustries.size === 0 || industryStockCounts.size === 0) {
      setSelectedIndustryStockCount(0);
      console.log("🔢 종목 수 계산: 0 (산업 선택 없음)");
      return;
    }

    // 캐시된 Map에서 종목 수 합산 (즉시 계산, API 호출 없음)
    let total = 0;
    selectedIndustries.forEach((industry) => {
      const count = industryStockCounts.get(industry) || 0;
      total += count;
    });

    setSelectedIndustryStockCount(total);
    console.log("🔢 종목 수 계산:", {
      선택된_산업_수: selectedIndustries.size,
      산업별_종목_합계: total,
      개별_선택_종목: selectedStocks.size,
      최종_합계: total + selectedStocks.size,
    });
  }, [selectedIndustries, industryStockCounts, selectedStocks.size]);

  // 백테스트 시작 핸들러
  const handleStartBacktest = async () => {
    try {
      setIsRunning(true);
      setError(null);

      const finalStrategyName = strategyName || defaultStrategyName;

      const request = {
        ...getBacktestRequest(),
        strategy_name: finalStrategyName,
      };

      console.log("=== 백테스트 요청 데이터 ===");
      console.log(JSON.stringify(request, null, 2));
      console.log("========================");

      const response = await runBacktest(request);

      console.log("=== 백테스트 응답 데이터 ===");
      console.log(JSON.stringify(response, null, 2));
      console.log("========================");

      const encodedStrategy = encodeURIComponent(finalStrategyName);
      router.push(`/quant/result/${response.backtestId}?strategyName=${encodedStrategy}`);
    } catch (err: any) {
      console.error("=== 백테스트 실행 실패 ===");
      console.error("Error:", err);
      console.error("Response data:", err.response?.data);
      console.error("Response status:", err.response?.status);
      console.error("========================");

      const errorMessage =
        err.response?.data?.message ||
        err.message ||
        "백테스트 실행 중 오류가 발생했습니다.";
      setError(errorMessage);
    } finally {
      setIsRunning(false);
    }
  };

  // 로딩 중일 때
  if (isLoadingIndustries) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-text-body">데이터를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div id="section-trade-target" className="space-y-6">
      {/* 헤더 */}
      <TradeTargetHeader
        selectedCount={finalSelectedCount}
        totalCount={finalTotalCount}
      />

      {/* 전략 이름 입력 */}
      <FieldPanel conditionType="target">
        <div className="space-y-2">
          <Title variant="subtitle">전략 이름</Title>
          <input
            type="text"
            value={strategyName || defaultStrategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            className="w-full px-4 py-2 border border-border-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary"
          />
        </div>
      </FieldPanel>

      {/* 매매 대상 종목 */}
      <FieldPanel conditionType="target">
        <StockCount
          selectedCount={finalSelectedCount}
          totalCount={finalTotalCount}
        />

        {/* 주식 유니버스 및 테마 선택 (DB 산업 데이터) */}
        <UniverseThemeSelection
          universes={universes}
          selectedUniverses={selectedUniverses}
          isAllUniversesSelected={isAllUniversesSelected}
          onToggleUniverse={toggleUniverse}
          onToggleAllUniverses={toggleAllUniverses}
          industries={industries}
          selectedIndustries={selectedIndustries}
          isAllIndustriesSelected={isAllIndustriesSelected}
          onToggleIndustry={toggleIndustry}
          onToggleAllIndustries={toggleAllIndustries}
        />
      </FieldPanel>

      {/* 종목 검색 및 테이블 */}
      <FieldPanel conditionType="target">
        <Title variant="subtitle">종목 검색</Title>

        {/* 검색 입력 */}
        <div className="my-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="종목명 또는 종목코드를 입력하세요 (예: 삼성전자, 005930)"
            className="w-full px-4 py-2 border border-border-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary"
          />
        </div>

        {/* 검색 결과 */}
        {isSearching && (
          <div className="text-center py-4 text-text-body">검색 중...</div>
        )}

        {!isSearching && searchQuery && searchResults.length === 0 && (
          <div className="text-center py-4 text-text-body">
            검색 결과가 없습니다.
          </div>
        )}

        {!isSearching && searchResults.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-bg-tertiary">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-semibold">
                    선택
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">
                    종목코드
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">
                    종목명
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">
                    산업
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">
                    시장
                  </th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((stock) => (
                  <tr
                    key={stock.stock_code}
                    className="border-b border-border-primary hover:bg-bg-secondary"
                  >
                    <td className="px-4 py-2">
                      <input
                        type="checkbox"
                        checked={selectedStocks.has(stock.stock_code)}
                        onChange={() => toggleStockSelection(stock.stock_code)}
                        className="w-4 h-4"
                      />
                    </td>
                    <td className="px-4 py-2 text-sm">{stock.stock_code}</td>
                    <td className="px-4 py-2 text-sm font-medium">
                      {stock.stock_name}
                    </td>
                    <td className="px-4 py-2 text-sm">{stock.industry}</td>
                    <td className="px-4 py-2 text-sm">
                      {stock.market_type || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 선택된 개별 종목 표시 */}
        {selectedStocks.size > 0 && (
          <div className="mt-4 p-4 bg-bg-secondary rounded-lg">
            <h4 className="text-sm font-semibold mb-2">
              개별 선택된 종목 ({selectedStocks.size}개)
            </h4>
            <div className="flex flex-wrap gap-2">
              {Array.from(selectedStocks).map((stockCode) => {
                const stock = searchResults.find(
                  (s) => s.stock_code === stockCode,
                );
                return (
                  <span
                    key={stockCode}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-accent-primary/10 text-accent-primary rounded-full text-sm"
                  >
                    {stock?.stock_name || stockCode}
                    <button
                      onClick={() => toggleStockSelection(stockCode)}
                      className="hover:text-accent-secondary"
                    >
                      ×
                    </button>
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </FieldPanel>

      {/* 에러 메시지 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* 백테스트 시작하기 버튼 */}
      <div className="flex justify-center pt-6">
        <button
          onClick={handleStartBacktest}
          disabled={isRunning}
          className={`px-12 py-4 rounded-lg text-lg font-bold transition-opacity ${
            isRunning
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-brand-purple text-white hover:opacity-90"
          }`}
        >
          {isRunning ? "백테스트 실행 중..." : "백테스트 시작하기"}
        </button>
      </div>
    </div>
  );
}
