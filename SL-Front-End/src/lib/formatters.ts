/**
 * 금액/퍼센트 포맷터 (계좌/요약 공용)
 */
export const formatAmount = (value: string | number): string => {
  const num = typeof value === "string"
    ? Number.parseInt(value.replace(/,/g, ""), 10)
    : value;
  if (Number.isNaN(num)) return "0";
  return num.toLocaleString("ko-KR");
};

export const formatPercent = (value: string | number, digits = 2): string => {
  const num = typeof value === "string"
    ? Number.parseFloat(value.replace(/,/g, ""))
    : value;
  if (Number.isNaN(num)) return "0.00";
  return num.toFixed(digits);
};

export const getProfitColor = (value: string | number): string => {
  const num = typeof value === "string" ? Number.parseFloat(value) : value;
  if (num > 0) return "text-price-up";
  if (num < 0) return "text-price-down";
  return "text-text-muted";
};
