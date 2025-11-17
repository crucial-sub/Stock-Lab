export type GuestPortfolioRank = "gold" | "silver" | "bronze";

export interface GuestPortfolioCardData {
  rank: number;
  name: string;
  organization: string;
  returnRate: number;
  highlight?: GuestPortfolioRank;
}

export interface GuestMarketIndex {
  label: string;
  value: string;
  change: string;
}

export interface GuestMarketStock {
  id: string;
  name: string;
  tag: string;
  change: string;
  price: string;
  volume: string;
}

export interface GuestMarketNews {
  id: string;
  title: string;
  badge: string;
}
