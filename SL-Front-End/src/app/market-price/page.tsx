import { MarketPriceContent } from "@/components/market-price/MarketPriceContent";

export default function MarketPricePage() {
  return (
    <section className="flex flex-col gap-[1.875rem] px-[18.75rem] py-[3.75rem]">
      {/* Figma 디자인: 28px font-semibold, 30px left margin */}
      <h1 className="text-[1.75rem] font-semibold text-black ml-[1.875rem] mb-10">
        국내 주식 시세
      </h1>
      <MarketPriceContent />
    </section>
  );
}
