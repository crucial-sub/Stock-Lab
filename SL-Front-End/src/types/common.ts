export interface Tab {
  id: string;
  label: string;
}

export interface SelectOption {
  value: string;
  label: string;
}

export type SortOrder = "asc" | "desc";
export type DataType = "daily" | "monthly";
export type PeriodType = "1d" | "1w" | "1m" | "3m" | "6m" | "1y";
