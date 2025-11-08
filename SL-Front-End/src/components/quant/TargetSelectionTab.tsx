"use client";

import { useThemesQuery } from "@/hooks/useThemesQuery";
import { useBacktestConfigStore } from "@/stores";
import Image from "next/image";
import { useEffect, useState } from "react";

/**
 * 매매 대상 선택 탭 - 새 디자인
 *
 * ThreeColumnLayout을 사용한 완전히 새로운 구현:
 * - 왼쪽: 네비게이션 사이드바
 * - 중앙: 매매 대상 선택 폼 (산업 선택, 테마 선택, 검색, 종목 테이블)
 * - 오른쪽: 설정 요약 패널
 */
export default function TargetSelectionTab() {
  // React Query로 테마 데이터 가져오기
  const { data: themes, isLoading: isLoadingThemes } = useThemesQuery();

  // Zustand store
  const { target_stocks } = useBacktestConfigStore();

  // 사이드바 상태
  const [activeSection, setActiveSection] = useState("매매 대상 설정");
  const sidebarItems = [
    "매수 조건",
    "매도 조건",
    "  목표가 / 손절가",
    "  보유 기간",
    "  조건 매도",
    "매매 대상 설정",
  ];

  // 선택된 산업 및 테마
  const [selectedIndustries, setSelectedIndustries] = useState<Set<string>>(
    new Set(["전체선택"])
  );
  const [selectedThemes, setSelectedThemes] = useState<Set<string>>(
    new Set(["전체선택"])
  );

  // 검색어
  const [searchQuery, setSearchQuery] = useState("");

  // 산업 목록 (하드코딩 - Figma 디자인 기준)
  const industries = [
    "전체선택",
    "코스피 대형",
    "코스피 중대형",
    "코스피 중형",
    "코스피 중소형",
    "코스피 소형",
    "코스피 초소형",
  ];

  // 테마 목록 (하드코딩 - Figma 디자인 기준)
  const themeOptions = [
    { id: "전체선택", name: "전체선택" },
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

  // 모의 주식 데이터
  const mockStocks = [
    {
      name: "삼성전자",
      theme: "전기 / 전자",
      code: "005930",
      price: "99,600원",
      change: "-0.99%",
    },
    {
      name: "삼성바이오로직스",
      theme: "제약",
      code: "207940",
      price: "1,221,000원",
      change: "0%",
    },
    {
      name: "삼성SDI",
      theme: "IT 서비스",
      code: "006400",
      price: "320,500원",
      change: "-1.38%",
    },
    {
      name: "삼성물산",
      theme: "유통",
      code: "028260",
      price: "218,500원",
      change: "+1.39%",
    },
    {
      name: "삼성화재",
      theme: "유통",
      code: "028260",
      price: "218,500원",
      change: "+1.39%",
    },
  ];

  // 산업 토글
  const toggleIndustry = (industry: string) => {
    const newSelected = new Set(selectedIndustries);
    if (industry === "전체선택") {
      if (newSelected.has("전체선택")) {
        newSelected.clear();
      } else {
        newSelected.clear();
        newSelected.add("전체선택");
      }
    } else {
      newSelected.delete("전체선택");
      if (newSelected.has(industry)) {
        newSelected.delete(industry);
      } else {
        newSelected.add(industry);
      }
    }
    setSelectedIndustries(newSelected);
  };

  // 테마 토글
  const toggleTheme = (themeId: string) => {
    const newSelected = new Set(selectedThemes);
    if (themeId === "전체선택") {
      if (newSelected.has("전체선택")) {
        newSelected.clear();
      } else {
        newSelected.clear();
        newSelected.add("전체선택");
      }
    } else {
      newSelected.delete("전체선택");
      if (newSelected.has(themeId)) {
        newSelected.delete(themeId);
      } else {
        newSelected.add(themeId);
      }
    }
    setSelectedThemes(newSelected);
  };

  // 선택된 테마를 전역 스토어에 업데이트
  useEffect(() => {
    const themeNames = Array.from(selectedThemes);
    useBacktestConfigStore.setState({ target_stocks: themeNames });
  }, [selectedThemes]);

  // 메인 컨텐츠
  const mainContent = (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-text-strong mb-2">
          매매 대상 설정
        </h2>
        <p className="text-sm text-text-body">
          매매할 대상을 선택합니다. 여러 대상을 한번에길 있는 종목을 배제할
          수도 있고 종목별로 배제할 수도 있습니다.
        </p>
      </div>

      {/* 매매 대상 종목 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <div className="mb-4">
          <span className="text-lg font-bold text-text-strong">
            매매 대상 종목
          </span>
          <span className="ml-3 text-accent-primary font-bold">
            2539 종목 / 3580 종목
          </span>
          <span className="ml-2 text-sm text-text-body">(선택 / 전체)</span>
        </div>

        {/* 주식 유니버스 선택 */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-3">
            <h4 className="text-base font-semibold text-text-strong">
              주식 유니버스 선택
            </h4>
            <button
              onClick={() => toggleIndustry("전체선택")}
              className="flex items-center gap-2"
            >
              <div
                className={`w-5 h-5 rounded border-2 flex items-center justify-center ${selectedIndustries.has("전체선택")
                  ? "bg-accent-primary border-accent-primary"
                  : "border-border-default"
                  }`}
              >
                {selectedIndustries.has("전체선택") && (
                  <Image
                    src="/icons/check_box.svg"
                    alt=""
                    width={16}
                    height={16}
                  />
                )}
              </div>
              <span className="text-sm text-accent-primary">전체선택</span>
            </button>
          </div>

          <div className="grid grid-cols-6 gap-3">
            {industries.slice(1).map((industry) => (
              <button
                key={industry}
                onClick={() => toggleIndustry(industry)}
                className="flex items-center gap-2"
              >
                <div
                  className={`w-5 h-5 rounded border-2 flex items-center justify-center ${selectedIndustries.has(industry)
                    ? "bg-accent-primary border-accent-primary"
                    : "border-border-default"
                    }`}
                >
                  {selectedIndustries.has(industry) && (
                    <Image
                      src="/icons/check_box.svg"
                      alt=""
                      width={16}
                      height={16}
                    />
                  )}
                </div>
                <span className="text-sm text-text-body">{industry}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 주식 테마 선택 */}
        <div>
          <div className="flex items-center gap-3 mb-3">
            <h4 className="text-base font-semibold text-text-strong">
              주식 테마 선택
            </h4>
            <button
              onClick={() => toggleTheme("전체선택")}
              className="flex items-center gap-2"
            >
              <div
                className={`w-5 h-5 rounded border-2 flex items-center justify-center ${selectedThemes.has("전체선택")
                  ? "bg-accent-primary border-accent-primary"
                  : "border-border-default"
                  }`}
              >
                {selectedThemes.has("전체선택") && (
                  <Image
                    src="/icons/check_box.svg"
                    alt=""
                    width={16}
                    height={16}
                  />
                )}
              </div>
              <span className="text-sm text-accent-primary">전체선택</span>
            </button>
          </div>

          <div className="grid grid-cols-6 gap-3">
            {themeOptions.slice(1).map((theme) => (
              <button
                key={theme.id}
                onClick={() => toggleTheme(theme.id)}
                className="flex items-center gap-2"
              >
                <div
                  className={`w-5 h-5 rounded border-2 flex items-center justify-center ${selectedThemes.has(theme.id)
                    ? "bg-accent-primary border-accent-primary"
                    : "border-border-default"
                    }`}
                >
                  {selectedThemes.has(theme.id) && (
                    <Image
                      src="/icons/check_box.svg"
                      alt=""
                      width={16}
                      height={16}
                    />
                  )}
                </div>
                <span className="text-sm text-text-body">{theme.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 검색 */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="종목 이름으로 검색하기"
          className="flex-1 px-4 py-3 bg-bg-surface border border-border-default rounded-sm text-text-body placeholder:text-text-muted focus:outline-none focus:border-accent-primary"
        />
        <button
          type="button"
          className="px-4 py-3 bg-bg-surface border border-border-default rounded-sm hover:bg-bg-muted transition-colors"
        >
          <Image src="/icons/search.svg" alt="검색" width={20} height={20} />
        </button>
      </div>

      {/* 종목 테이블 */}
      <div className="bg-bg-surface rounded-lg shadow-card overflow-hidden">
        {/* 테이블 헤더 */}
        <div className="grid grid-cols-[60px_1fr_200px_150px_150px_150px_150px] gap-4 px-6 py-4 bg-bg-muted border-b border-border-subtle">
          <div className="text-sm font-medium text-text-muted">선택</div>
          <div className="text-sm font-medium text-text-muted">종목 이름</div>
          <div className="text-sm font-medium text-text-muted">테마</div>
          <div className="text-sm font-medium text-text-muted">종목 코드</div>
          <div className="text-sm font-medium text-text-muted text-right">
            전일 종가
          </div>
          <div className="text-sm font-medium text-text-muted text-right">
            시장 등락률
          </div>
        </div>

        {/* 테이블 바디 */}
        <div>
          {mockStocks.map((stock) => {
            const isNegative = stock.change.startsWith("-");
            return (
              <div
                key={`${stock.code}-${stock.name}`}
                className="grid grid-cols-[60px_1fr_200px_150px_150px_150px_150px] gap-4 px-6 py-4 border-b border-border-subtle hover:bg-bg-muted transition-colors"
              >
                {/* 체크박스 */}
                <div className="flex items-center justify-center">
                  <button className="w-6 h-6">
                    <Image
                      src="/icons/check_box_blank.svg"
                      alt=""
                      width={24}
                      height={24}
                    />
                  </button>
                </div>

                {/* 종목 이름 */}
                <div className="flex items-center text-text-body">
                  {stock.name}
                </div>

                {/* 테마 */}
                <div className="flex items-center text-text-body">
                  {stock.theme}
                </div>

                {/* 종목 코드 */}
                <div className="flex items-center text-text-body">
                  {stock.code}
                </div>

                {/* 전일 종가 */}
                <div className="flex items-center justify-end text-text-body">
                  {stock.price}
                </div>

                {/* 시장 등락률 */}
                <div
                  className={`flex items-center justify-end font-semibold ${isNegative ? "text-accent-primary" : "text-brand-primary"
                    }`}
                >
                  {stock.change}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 백테스트 시작하기 버튼 */}
      <div className="flex justify-center pt-6">
        <button className="px-12 py-4 bg-accent-primary text-white rounded-lg text-lg font-bold hover:opacity-90 transition-opacity">
          백테스트 시작하기
        </button>
      </div>
    </div>
  );

  if (isLoadingThemes) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-text-body">데이터를 불러오는 중...</div>
      </div>
    );
  }

  return mainContent;
}
