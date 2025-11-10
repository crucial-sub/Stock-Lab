import { useState } from "react";
import Image from "next/image";
import { FieldPanel } from "../common";

/**
 * 종목 검색 및 테이블 섹션
 * - 종목 검색 기능
 * - 종목 목록 테이블
 */
interface Stock {
  name: string;
  theme: string;
  code: string;
  price: string;
  change: string;
}

interface StockSearchAndTableProps {
  stocks: Stock[];
}

export function StockSearchAndTable({ stocks }: StockSearchAndTableProps) {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <>
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
      <FieldPanel conditionType="target" className="p-0 overflow-hidden">
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
          {stocks.map((stock, index) => {
            const isNegative = stock.change.startsWith("-");
            return (
              <div
                key={`${stock.code}-${index}`}
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
                  className={`flex items-center justify-end font-semibold ${
                    isNegative ? "text-accent-primary" : "text-brand-primary"
                  }`}
                >
                  {stock.change}
                </div>
              </div>
            );
          })}
        </div>
      </FieldPanel>
    </>
  );
}
