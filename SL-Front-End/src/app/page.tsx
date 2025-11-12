"use client";

import type { NextPage } from "next";
import { useEffect, useState } from "react";

import { FeaturedStrategiesSection } from "@/components/home/FeaturedStrategiesSection";
import type { MarketTickerCardProps } from "@/components/home/MarketTickerCard";
import type { NewsItem } from "@/components/home/NewsCard";
import type { StrategyCardProps } from "@/components/home/StrategyCard";
import { TodayMarketSection } from "@/components/home/TodayMarketSection";
import { TodayNewsSection } from "@/components/home/TodayNewsSection";
import { StockDetailModal } from "@/components/modal/StockDetailModal";
import { marketQuoteApi } from "@/lib/api/market-quote";

const featuredStrategies: StrategyCardProps[] = [
    {
        title: "전략 이름",
        author: "nickname",
        tags: ["태그1", "태그2"],
        description:
            "전략을 소개하는 설명이 들어갑니다. Simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the...",
        metrics: [
            { label: "수익률", value: "99.99%", tone: "positive" },
            { label: "MDD", value: "40%", tone: "muted" },
            { label: "일 평균 수익률", value: "99.99%", tone: "positive" },
        ],
        ctaLabel: "전략 확인하기",
    },
    {
        title: "전략 이름",
        author: "nickname",
        tags: ["태그1", "태그2"],
        description:
            "전략을 소개하는 설명이 들어갑니다. Simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the...",
        metrics: [
            { label: "수익률", value: "99.99%", tone: "positive" },
            { label: "MDD", value: "40%", tone: "muted" },
            { label: "일 평균 수익률", value: "99.99%", tone: "positive" },
        ],
        ctaLabel: "전략 확인하기",
    },
    {
        title: "전략 이름",
        author: "nickname",
        tags: ["태그1", "태그2"],
        description:
            "전략을 소개하는 설명이 들어갑니다. Simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the...",
        metrics: [
            { label: "수익률", value: "99.99%", tone: "positive" },
            { label: "MDD", value: "40%", tone: "muted" },
            { label: "일 평균 수익률", value: "99.99%", tone: "positive" },
        ],
        ctaLabel: "전략 확인하기",
    },
];


const newsItems: NewsItem[] = [
    {
        id: "news-1",
        title: "제목의 위치는 여기입니다.",
        nameTag: "종목 이름",
        SentimentTag: "긍정",
        publishedAt: "30분 전",
        source: "www.naver.com/example/link",
        summary:
            "여기에 간단한 내용이 들어갑니다. Simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the...",
    },
    {
        id: "news-2",
        title: "제목의 위치는 여기입니다.",
        nameTag: "종목 이름",
        SentimentTag: "긍정",
        publishedAt: "30분 전",
        source: "www.naver.com/example/link",
        summary:
            "여기에 간단한 내용이 들어갑니다. Simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the...",
    },
    {
        id: "news-3",
        title: "제목의 위치는 여기입니다.",
        nameTag: "종목 이름",
        SentimentTag: "긍정",
        publishedAt: "30분 전",
        source: "www.naver.com/example/link",
        summary:
            "여기에 간단한 내용이 들어갑니다. Simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the...",
    },
];

const HomePage: NextPage = () => {
    const [marketTickers, setMarketTickers] = useState<MarketTickerCardProps[]>([]);
    const [selectedStock, setSelectedStock] = useState<{ name: string; code: string } | null>(null);

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                const response = await marketQuoteApi.getMarketQuotes({
                    sortBy: "change_rate",
                    sortOrder: "desc",
                    page: 1,
                    pageSize: 20,
                });

                const formattedTickers: MarketTickerCardProps[] = response.items.map((item) => ({
                    id: item.code,
                    name: item.name,
                    code: item.code,
                    price: `${item.price.toLocaleString()}원`,
                    change: `${item.changeRate > 0 ? "+" : ""}${item.changeRate.toFixed(2)}%`,
                    trend: item.trend === "up" ? "up" : "down",
                    logoSrc: "/icons/krafton-logo.svg", // 기본 로고 (추후 개선 가능)
                    graph: item.trend === "up" ? "/icons/up-graph.svg" : "/icons/down-graph.svg",
                    onDetailClick: () => setSelectedStock({ name: item.name, code: item.code }),
                }));

                setMarketTickers(formattedTickers);
            } catch (error) {
                console.error("시장 데이터 조회 실패:", error);
            }
        };

        fetchMarketData();
    }, []);

    return (
        <>
            <div className="">
                <div className="flex w-full flex-col gap-10 md:px-10 lg:px-0" >
                    <FeaturedStrategiesSection strategies={featuredStrategies} />
                    <TodayMarketSection items={marketTickers} />
                    <TodayNewsSection items={newsItems} />
                </div >
            </div >

            <StockDetailModal
                isOpen={!!selectedStock}
                onClose={() => setSelectedStock(null)}
                stockName={selectedStock?.name || ""}
                stockCode={selectedStock?.code || ""}
            />
        </>
    );
};

export default HomePage;
