"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";
import { MOCK_SCRIPTS } from "@/constants";

export default function QuantPage() {
  const [selectedScripts, setSelectedScripts] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredScript, setHoveredScript] = useState<number | null>(null);
  const [sortDescending, setSortDescending] = useState(true);

  const toggleScript = (id: number) => {
    setSelectedScripts((prev) =>
      prev.includes(id) ? prev.filter((sid) => sid !== id) : [...prev, id],
    );
  };

  const toggleSortOrder = () => {
    setSortDescending((prev) => !prev);
  };

  const handleDeleteSelected = () => {
    if (!selectedScripts.length) return;
    // TODO: Integrate with delete workflow once API is available.
  };

  const sortedScripts = useMemo(() => {
    const scripts = [...MOCK_SCRIPTS];
    return sortDescending ? scripts : scripts.reverse();
  }, [sortDescending]);

  return (
    <div className="w-[1000px] quant-container pt-[40px] space-y-6">
      {/* Page Title */}
      <h1 className="section-title">내가 만든 전략</h1>

      {/* Actions and Search */}
      <div className="flex items-center justify-between">
        {/* Actions */}
        <div className="flex items-center gap-2">
          <Link
            href="/quant/new"
            className="quant-button-secondary inline-flex"
          >
            전략 새로 만들기
          </Link>
          <button
            type="button"
            className="quant-button-secondary"
            onClick={handleDeleteSelected}
            disabled={selectedScripts.length === 0}
          >
            선택 전략 삭제
          </button>
          <button
            type="button"
            className="quant-button-secondary"
            onClick={toggleSortOrder}
          >
            정렬 순서 바꾸기
          </button>
        </div>

        {/* Search */}
        <div className="flex items-center gap-0">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="전략 이름으로 검색"
            className="search-input w-[180px] mr-[20px]"
          />
          <button type="button" className="search-button" aria-label="검색">
            <Image src="/icons/search.svg" alt="" width={20} height={20} />
          </button>
        </div>
      </div>
      <div className="px-[12px] pt-[24px] text-[0.9rem] text-text-tertiary">
        <span className="text-text-tertiary">전략 이름</span>
        <span className="text-text-tertiary ml-[312px]">일 평균 수익률</span>
        <span className="text-text-tertiary ml-[88px]">누적 수익률</span>
        <span className="text-text-tertiary ml-[112px]">최종 수정일</span>
        <span className="text-text-tertiary ml-[124px]">생성일</span>
      </div>

      {/* Script List */}
      <div className="space-y-4">
        {sortedScripts.map((script) => {
          const isHovered = hoveredScript === script.id;
          const isSelected = selectedScripts.includes(script.id);

          return (
            <button
              key={script.id}
              className={`list-item ${isSelected ? "is-selected" : ""}`}
              type="button"
              onMouseEnter={() => setHoveredScript(script.id)}
              onMouseLeave={() => setHoveredScript(null)}
              onClick={() => toggleScript(script.id)}
              aria-pressed={isSelected}
            >
              <div className="flex w-full items-center gap-6 px-[0px] text-[1.1rem]">
                {/* Checkbox */}
                <div className="flex w-[60px] items-center justify-center">
                  <Image
                    src={isSelected ? "/icons/check_box.svg" : "/icons/check_box_outline_blank.svg"}
                    alt=""
                    width={24}
                    height={24}
                    aria-hidden="true"
                  />
                </div>

                {/* Script Name */}
                <div
                  className={`flex w-[220px] text-[1.3rem] items-center font-medium ${isHovered ? "text-hover" : "text-normal"}`}
                >
                  {script.name}
                </div>

                {/* 일 평균 수익률 */}
                <div
                  className={`flex flex-1 text-[1.3rem] items-center justify-end font-medium ${
                    script.avgReturn >= 0
                      ? isHovered
                        ? "value-positive"
                        : "value-positive-normal"
                      : isHovered
                        ? "value-negative"
                        : "value-negative-normal"
                  }`}
                >
                  {script.avgReturn >= 0 ? "+" : ""}
                  {script.avgReturn}%
                </div>

                {/* 누적 수익률 */}
                <div
                  className={`flex flex-1 text-[1.3rem] items-center justify-end font-medium ${
                    script.totalReturn >= 0
                      ? isHovered
                        ? "value-positive"
                        : "value-positive-normal"
                      : isHovered
                        ? "value-negative"
                        : "value-negative-normal"
                  }`}
                >
                  {script.totalReturn >= 0 ? "+" : ""}
                  {script.totalReturn}%
                </div>

                {/* 최종 수정일 */}
                <div
                  className={`flex w-[150px] items-center justify-end text-[0.9rem] ${
                    isHovered ? "text-hover" : "text-normal"
                  }`}
                >
                  {script.editDate}
                </div>

                {/* 생성일 */}
                <div
                  className={`flex w-[150px] items-center justify-end text-[0.9rem] pr-[12px] ${
                    isHovered ? "text-hover" : "text-normal"
                  }`}
                >
                  {script.createDate}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Divider */}
      <div className="h-px bg-border-subtle" />
    </div>
  );
}
