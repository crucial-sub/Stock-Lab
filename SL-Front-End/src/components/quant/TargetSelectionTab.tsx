"use client";

/**
 * 매매 대상 선택 탭 - DB 연동 버전
 *
 * 개선 사항:
 * - 실제 DB의 industry 컬럼에서 데이터 로드
 * - API 연동으로 실제 종목 데이터 표시
 * - 커스텀 훅으로 비즈니스 로직 분리
 */

import { useBacktestConfigStore } from "@/stores";
import { useState, useEffect } from "react";
import { runBacktest } from "@/lib/api/backtest";
import { getIndustries, getStocksByIndustries, searchStocks, type StockInfo } from "@/lib/api/industries";
import { useRouter } from "next/navigation";
import { useTradeTargetSelection } from "@/hooks/quant";
import {
  TradeTargetHeader,
  StockCount,
  UniverseThemeSelection,
  StockSearchAndTable,
} from "@/components/quant/sections";

export default function TargetSelectionTab() {
  const { getBacktestRequest } = useBacktestConfigStore();
  const router = useRouter();

  // 산업 데이터 상태 (DB에서 가져옴)
  const [industries, setIndustries] = useState<string[]>([]);
  const [industryStockCounts, setIndustryStockCounts] = useState<Map<string, number>>(new Map());
  const [isLoadingIndustries, setIsLoadingIndustries] = useState(true);
  const [totalStockCount, setTotalStockCount] = useState(0);

  // 종목 검색 및 선택 상태
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<StockInfo[]>([]);
  const [selectedStocks, setSelectedStocks] = useState<Set<string>>(new Set());
  const [isSearching, setIsSearching] = useState(false);

  // 백테스트 실행 상태
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
  const [selectedIndustryStockCount, setSelectedIndustryStockCount] = useState(0);

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
    selectedIndustryStockCount + selectedStocks.size, // 최종 선택된 종목 수
    totalStockCount
  );

  // 최종 선택된 종목 수 = 체크박스로 선택된 산업의 종목 + 개별 검색으로 선택된 종목
  const finalSelectedCount = selectedIndustryStockCount + selectedStocks.size;

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
      최종_합계: total + selectedStocks.size
    });
  }, [selectedIndustries, industryStockCounts, selectedStocks.size]);

  // 백테스트 시작 핸들러
  const handleStartBacktest = async () => {
    try {
      setIsRunning(true);
      setError(null);

      const request = getBacktestRequest();

      console.log("=== 백테스트 요청 데이터 ===");
      console.log(JSON.stringify(request, null, 2));
      console.log("========================");

      const response = await runBacktest(request);

      console.log("=== 백테스트 응답 데이터 ===");
      console.log(JSON.stringify(response, null, 2));
      console.log("========================");

      router.push(`/quant/result/${response.backtestId}`);
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
        totalCount={totalStockCount}
      />

      {/* 매매 대상 종목 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <StockCount
          selectedCount={finalSelectedCount}
          totalCount={totalStockCount}
        />

        {/* 주식 테마 선택 (DB 산업 데이터) */}
        <UniverseThemeSelection
          industries={industries}
          selectedIndustries={selectedIndustries}
          isAllIndustriesSelected={isAllIndustriesSelected}
          onToggleIndustry={toggleIndustry}
          onToggleAllIndustries={toggleAllIndustries}
        />
      </div>

      {/* 종목 검색 및 테이블 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <h3 className="text-lg font-semibold mb-4">종목 검색</h3>

        {/* 검색 입력 */}
        <div className="mb-4">
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
                  <th className="px-4 py-2 text-left text-sm font-semibold">선택</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">종목코드</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">종목명</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">산업</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">시장</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((stock) => (
                  <tr key={stock.stock_code} className="border-b border-border-primary hover:bg-bg-secondary">
                    <td className="px-4 py-2">
                      <input
                        type="checkbox"
                        checked={selectedStocks.has(stock.stock_code)}
                        onChange={() => toggleStockSelection(stock.stock_code)}
                        className="w-4 h-4"
                      />
                    </td>
                    <td className="px-4 py-2 text-sm">{stock.stock_code}</td>
                    <td className="px-4 py-2 text-sm font-medium">{stock.stock_name}</td>
                    <td className="px-4 py-2 text-sm">{stock.industry}</td>
                    <td className="px-4 py-2 text-sm">{stock.market_type || "-"}</td>
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
                const stock = searchResults.find((s) => s.stock_code === stockCode);
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
      </div>

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
              : "bg-accent-primary text-white hover:opacity-90"
          }`}
        >
          {isRunning ? "백테스트 실행 중..." : "백테스트 시작하기"}
        </button>
      </div>
    </div>
  );
}
