import { Title } from "@/components/common/Title";
import { StrategyCard, type StrategyCardProps } from "./StrategyCard";

interface FeaturedStrategiesSectionProps {
  strategies: StrategyCardProps[];
  className?: string;
}

export function FeaturedStrategiesSection({
  strategies,
  className = "",
}: FeaturedStrategiesSectionProps) {
  return (
    <section className={`flex flex-col gap-5 ${className}`}>
      <Title>에디터가 추천하는 수익률이 높은 전략</Title>
      <div className="flex flex-nowrap gap-10 w-full">
        {strategies.map((strategy, index) => (
          <div
            key={`${strategy.title}-${index}`}
            className="basis-[calc((100%-5rem)/3)]"
          >
            <StrategyCard {...strategy} />
          </div>
        ))}
      </div>
    </section>
  );
}
