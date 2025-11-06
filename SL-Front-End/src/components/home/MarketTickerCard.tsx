import Image from "next/image";
import Link from "next/link";
import { Icon } from "../common/Icon";

export interface MarketTickerCardProps {
  id: string;
  name: string;
  code: string;
  price: string;
  change: string;
  trend: "up" | "down";
  logoSrc?: string;
  logoAlt?: string;
  graph?: string;
}

export function MarketTickerCard({
  name,
  code,
  price,
  change,
  trend,
  logoSrc = "",
  logoAlt = "",
  graph = ""
}: MarketTickerCardProps) {
  const changeColor = trend === "up" ? "text-[#FF6464]" : "text-[#4C7CFF]";

  return (
    <article
      className={`flex w-full items-center gap-6 rounded-sm px-5 py-3 shadow-[0px_0px_8px_rgba(0,0,0,0.1)] ${trend === "up" ? "bg-[#FFF6F6]" : "bg-[#EFF6FF]"}`}
    >
      <div className="flex flex-shrink-0 gap-3">
        <Image src={logoSrc} alt={logoAlt} width={60} height={60} />
        <div className="flex flex-col gap-1 justify-center">
          <span className="justify-center text-xl font-semibold">{name}</span>
          <span className="justify-center text-base font-light">{code}</span>
        </div>
      </div>
      <Image src={graph} alt={""} width={70} height={16} className="flex" />
      <div className="flex flex-shrink-0 items-center justify-end gap-6">
        <div className="flex flex-col items-end gap-1">
          <span className="text-xl font-semibold text-[#111827]">{price}</span>
          <span className={`text-sm font-medium ${changeColor}`}>{change}</span>
        </div>
      </div>
      <div className="flex flex-shrink-0 items-center">
        <Link href="#" className="flex items-center gap-1 text-base font-light">
          <span>자세히 보기</span>
          <Icon src="/icons/arrow-right.svg" size={20} />
        </Link>
      </div>
    </article>
  );
}
