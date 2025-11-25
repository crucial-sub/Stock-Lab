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

export interface GuestCommunityPost {
  id: string;
  title: string;
  preview: string;
  author: string;
  date: string;
  tag: string;
  views: string;
  likes: string;
  comments: string;
}

export interface HomeStatCardData {
  id: string;
  title: string;
  value: string;
  change: string;
  badge?: string;
  description?: string;
}

export interface MarketStock {
  id: string;
  name: string;
  tag: string;
  change: string;
  changeRate: number;
  price: string;
  volume: string;
}

export interface MarketNews {
  id: string;
  title: string;
  badge: string;
}

export interface HomePortfolioHighlight {
  id: string;
  name: string;
  returnRate: number;
  rank: number;
}

export interface HomeCommunityHighlight {
  id: string;
  title: string;
  preview: string;
  tag: string;
  views: string;
  likes: string;
  comments: string;
}
