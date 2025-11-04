import { useState } from "react";
import { MOCK_FACTOR_CATEGORIES } from "@/constants";

export function useFactorModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("investment");
  const [searchQuery, setSearchQuery] = useState("");

  const currentCategory = MOCK_FACTOR_CATEGORIES.find(
    (c) => c.id === selectedCategory,
  );

  const open = () => setIsOpen(true);
  const close = () => {
    setIsOpen(false);
    setSearchQuery("");
  };

  return {
    isOpen,
    open,
    close,
    selectedCategory,
    setSelectedCategory,
    searchQuery,
    setSearchQuery,
    currentCategory,
    categories: MOCK_FACTOR_CATEGORIES,
  };
}
