import type { NextPage } from "next";

import { FeaturedStrategiesSection } from "@/components/home/FeaturedStrategiesSection";
import type { MarketTickerCardProps } from "@/components/home/MarketTickerCard";
import type { NewsItem } from "@/components/home/NewsCard";
import type { StrategyCardProps } from "@/components/home/StrategyCard";
import { TodayMarketSection } from "@/components/home/TodayMarketSection";
import { TodayNewsSection } from "@/components/home/TodayNewsSection";

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

const marketTickers: MarketTickerCardProps[] = [
    {
        id: "krafton-1",
        name: "Krafton",
        code: "259960",
        price: "263,500원",
        change: "+5.55%",
        trend: "up",
        logoSrc: "/icons/krafton-logo.svg",
        graph: "icons/up-graph.svg"
    },
    {
        id: "samsung-1",
        name: "삼성전자",
        code: "005930",
        price: "99,500원",
        change: "-6.09%",
        trend: "down",
        logoSrc: "/icons/samsung-logo.svg",
        graph: "icons/down-graph.svg"
    },
    {
        id: "krafton-2",
        name: "Krafton",
        code: "259960",
        price: "263,500원",
        change: "+5.55%",
        trend: "up",
        logoSrc: "/icons/krafton-logo.svg",
        graph: "icons/up-graph.svg"
    },
    {
        id: "samsung-2",
        name: "삼성전자",
        code: "005930",
        price: "99,500원",
        change: "-6.09%",
        trend: "down",
        logoSrc: "/icons/samsung-logo.svg",
        graph: "icons/down-graph.svg"
    },
    {
        id: "krafton-3",
        name: "Krafton",
        code: "259960",
        price: "263,500원",
        change: "+5.55%",
        trend: "up",
        logoSrc: "/icons/krafton-logo.svg",
        graph: "icons/up-graph.svg"
    },
    {
        id: "samsung-3",
        name: "삼성전자",
        code: "005930",
        price: "99,500원",
        change: "-6.09%",
        trend: "down",
        logoSrc: "/icons/samsung-logo.svg",
        graph: "icons/down-graph.svg"
    },
    {
        id: "krafton-4",
        name: "Krafton",
        code: "259960",
        price: "263,500원",
        change: "+5.55%",
        trend: "up",
        logoSrc: "icons/krafton-logo.svg",
        graph: "icons/up-graph.svg"
    },
    {
        id: "samsung-4",
        name: "삼성전자",
        code: "005930",
        price: "99,500원",
        change: "-6.09%",
        trend: "down",
        logoSrc: "icons/samsung-logo.svg",
        graph: "icons/down-graph.svg"
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
    return (
        <div className="">
            <div className="flex w-full flex-col gap-10 md:px-10 lg:px-0" >
                <FeaturedStrategiesSection strategies={featuredStrategies} />
                <TodayMarketSection items={marketTickers} />
                <TodayNewsSection items={newsItems} />
            </div >
        </div >
    );
};

export default HomePage;
