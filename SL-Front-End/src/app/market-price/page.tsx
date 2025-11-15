import { MarketPriceContent } from "@/components/market-price/MarketPriceContent";

export default function MarketPricePage() {
  return (
    <section className="flex flex-col gap-4">
      <h1 className="text-[1.8rem] font-semibold text-text-strong">
        국내 주식 시세
      </h1>
      <MarketPriceContent />
    </section>
  );
}
