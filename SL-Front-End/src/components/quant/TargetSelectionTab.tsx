"use client";

/**
 * 매매 대상 선택 탭 - DB 연동 버전
 *
 * 개선 사항:
 * - 실제 DB의 industry 컬럼에서 데이터 로드
 * - API 연동으로 실제 종목 데이터 표시
 * - 커스텀 훅으로 비즈니스 로직 분리
 */

import { useThemesQuery } from "@/hooks/useThemesQuery";
import { useBacktestConfigStore } from "@/stores";
import { useState, useEffect } from "react";
import { runBacktest } from "@/lib/api/backtest";
import { getIndustries } from "@/lib/api/industries";
import { useRouter } from "next/navigation";
import { useTradeTargetSelection } from "@/hooks/quant";
import {
  TradeTargetHeader,
  StockCount,
  UniverseThemeSelection,
  StockSearchAndTable,
} from "./sections";

// 테마 목록도 API에서 가져올 예정 (현재는 목데이터)
const themeOptions = [
  { id: "건설", name: "건설" },
  { id: "금융", name: "금융" },
  { id: "기계 / 장비", name: "기계 / 장비" },
  { id: "농업 / 임업 / 어업", name: "농업 / 임업 / 어업" },
  { id: "보험사", name: "보험사" },
  { id: "비금속", name: "비금속" },
  { id: "섬유 / 의류", name: "섬유 / 의류" },
  { id: "운송 / 창고", name: "운송 / 창고" },
  { id: "은행", name: "은행" },
  { id: "유통", name: "유통" },
  { id: "운송설비 / 부품", name: "운송설비 / 부품" },
  { id: "의약 / 정밀기기", name: "의약 / 정밀기기" },
  { id: "전기 / 가스 / 수도", name: "전기 / 가스 / 수도" },
  { id: "종이 / 목재", name: "종이 / 목재" },
  { id: "증권", name: "증권" },
  { id: "출판 / 매체 복제", name: "출판 / 매체 복제" },
  { id: "통신", name: "통신" },
  { id: "IT 서비스", name: "IT 서비스" },
  { id: "기타 금융", name: "기타 금융" },
  { id: "기타 제조", name: "기타 제조" },
  { id: "기타", name: "기타" },
  { id: "제약", name: "제약" },
  { id: "화학", name: "화학" },
];

export default function TargetSelectionTab() {
  const { data: themes, isLoading: isLoadingThemes } = useThemesQuery();
  const { getBacktestRequest } = useBacktestConfigStore();
  const router = useRouter();

  // 산업 데이터 상태 (DB에서 가져옴)
  const [industries, setIndustries] = useState<string[]>([]);
  const [isLoadingIndustries, setIsLoadingIndustries] = useState(true);
  const [totalStockCount, setTotalStockCount] = useState(0);

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

  // 커스텀 훅으로 매매 대상 선택 로직 관리
  const {
    selectedIndustries,
    selectedThemes,
    isAllIndustriesSelected,
    isAllThemesSelected,
    toggleIndustry,
    toggleTheme,
    toggleAllIndustries,
    toggleAllThemes,
  } = useTradeTargetSelection(industries, themeOptions);

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

      router.push(`/quant/${response.backtestId}`);
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
  if (isLoadingThemes || isLoadingIndustries) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-text-body">데이터를 불러오는 중...</div>
      </div>
    );
  }

  // 선택된 산업의 종목 수 계산 (임시: 전체 종목 수 사용)
  const selectedStockCount = isAllIndustriesSelected
    ? totalStockCount
    : totalStockCount; // TODO: 선택된 산업의 실제 종목 수 계산

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <TradeTargetHeader
        selectedCount={selectedStockCount}
        totalCount={totalStockCount}
      />

      {/* 매매 대상 종목 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <StockCount
          selectedCount={selectedStockCount}
          totalCount={totalStockCount}
        />

        {/* 유니버스 및 테마 선택 */}
        <UniverseThemeSelection
          industries={industries}
          themeOptions={themeOptions}
          selectedIndustries={selectedIndustries}
          selectedThemes={selectedThemes}
          isAllIndustriesSelected={isAllIndustriesSelected}
          isAllThemesSelected={isAllThemesSelected}
          onToggleIndustry={toggleIndustry}
          onToggleTheme={toggleTheme}
          onToggleAllIndustries={toggleAllIndustries}
          onToggleAllThemes={toggleAllThemes}
        />
      </div>

      {/* 종목 검색 및 테이블 */}
      <StockSearchAndTable stocks={[]} />

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
