import { MarketPriceContent } from "@/components/market-price/MarketPriceContent";

export default function MarketPricePage() {
  return (
    <section className="flex flex-col gap-[1.875rem] px-4 sm:px-8 lg:px-12 xl:px-16 2xl:px-20 py-[3.75rem]">
      <div className="mx-auto w-full max-w-[1000px]">
        {/* Figma 디자인: 28px font-semibold, 30px left margin */}
        <span className="text-[1.5rem] font-semibold text-black ml-[1.875rem]">
          국내 주식 시세
        </span>
      </div>
      <MarketPriceContent />
    </section>
  );
}
