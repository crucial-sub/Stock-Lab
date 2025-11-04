import { useState } from "react";
import { MOCK_TARGET_STOCKS } from "@/constants";
import type { TargetStock } from "@/types";

export function useTargetStocks() {
  const [stocks, setStocks] = useState<TargetStock[]>(MOCK_TARGET_STOCKS);
  const [searchQuery, setSearchQuery] = useState("");

  const toggleStock = (id: number) => {
    setStocks((prev) =>
      prev.map((stock) =>
        stock.id === id ? { ...stock, selected: !stock.selected } : stock,
      ),
    );
  };

  const filteredStocks = stocks.filter((stock) =>
    stock.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return {
    stocks: filteredStocks,
    searchQuery,
    setSearchQuery,
    toggleStock,
  };
}
