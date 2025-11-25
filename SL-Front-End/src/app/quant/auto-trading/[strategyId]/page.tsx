import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { autoTradingApi } from "@/lib/api/auto-trading";
import { AutoTradingStatusPageClient } from "./AutoTradingStatusPageClient";

interface AutoTradingStatusPageProps {
  params: Promise<{
    strategyId: string;
  }>;
}

export default async function AutoTradingStatusPage({
  params,
}: AutoTradingStatusPageProps) {
  const { strategyId } = await params;

  // 로그인 여부 확인
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    redirect("/login?redirect=/quant");
  }

  try {
    // 가상매매 전략 상태 조회
    const axios = (await import("axios")).default;
    const baseURL = process.env.API_BASE_URL || "http://localhost:8000/api/v1";

    const response = await axios.get(
      `${baseURL}/auto-trading/strategies/${strategyId}/status`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const statusData = response.data;

    return (
      <AutoTradingStatusPageClient
        strategyId={strategyId}
        initialData={statusData}
      />
    );
  } catch (error: any) {
    // 401 에러: 로그인 페이지로 리다이렉트
    if (error?.response?.status === 401) {
      redirect("/login?redirect=/quant");
    }

    // 404 에러: 전략을 찾을 수 없음
    if (error?.response?.status === 404) {
      redirect("/quant");
    }

    console.error("Error fetching auto-trading status:", error);

    // 에러 발생 시 빈 데이터로 렌더링
    return (
      <AutoTradingStatusPageClient
        strategyId={strategyId}
        initialData={null}
      />
    );
  }
}
