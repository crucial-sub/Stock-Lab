"use client";

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
    <div className="quant-container py-8 space-y-6">
      {/* Page Title */}
      <h1 className="section-title">내가 만든 스크립트</h1>

      {/* Actions and Search */}
      <div className="flex items-center justify-between">
        {/* Actions */}
        <div className="flex items-center gap-2">
          <Link
            href="/quant/new"
            className="quant-button-secondary inline-flex"
          >
            스크립트 새로 만들기
          </Link>
          <button
            type="button"
            className="quant-button-secondary"
            onClick={handleDeleteSelected}
            disabled={selectedScripts.length === 0}
          >
            선택 스크립트 삭제
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
            placeholder="스크립트 이름으로 검색"
            className="search-input w-[200px]"
          />
          <button type="button" className="search-button">
            <span className="text-text-primary">🔍</span>
          </button>
        </div>
      </div>

      {/* Script List */}
      <div className="space-y-3">
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
              <div className="grid grid-cols-[44px_1fr_120px_150px] gap-6 items-center w-full px-5">
                {/* Checkbox and Divider */}
                <div className="flex items-center gap-3">
                  <span
                    className={`checkbox ${isSelected ? "is-checked" : ""}`}
                    aria-hidden="true"
                  />
                  <div
                    className="w-px h-8 bg-border-subtle"
                    aria-hidden="true"
                  />
                </div>

                {/* Script Name */}
                <div
                  className={`text-base font-medium ${isHovered ? "text-hover" : "text-normal"}`}
                >
                  {script.name}
                </div>

                {/* Return Rate */}
                <div
                  className={`text-base font-medium text-right ${
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

                {/* Date */}
                <div
                  className={`text-sm text-right ${isHovered ? "text-hover" : "text-normal"}`}
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
