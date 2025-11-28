"use client";

import { formatAmount, formatPercent, getProfitColor } from "@/lib/formatters";

interface KiwoomAccountSummaryProps {
  account: {
    cash?: {
      balance?: string | number;
      withdrawable?: string | number;
    };
    holdings?: {
      tot_prft_rt?: string | number;
      tot_evlt_amt?: string | number;
    };
  } | null;
}

export function KiwoomAccountSummary({ account }: KiwoomAccountSummaryProps) {
  if (!account?.holdings) return null;

  const cashBalance = account.cash?.balance ?? 0;
  const withdrawable = account.cash?.withdrawable ?? 0;
  const totalReturn = account.holdings?.tot_prft_rt ?? 0;
  const evaluationAmount = account.holdings?.tot_evlt_amt ?? 0;

  return (
    <section className="rounded-[12px] border border-[#18223433] bg-[#1822340D] p-5 shadow-elev-card">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text-body">연동 계좌 요약</h3>
        <span className="text-sm text-text-muted">프로필과 동일한 실시간 잔고</span>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg bg-white/40 p-4 shadow-elev-card-soft">
          <p className="text-xs text-text-muted mb-1">예수금</p>
          <p className="text-xl font-bold text-text-body">
            {formatAmount(cashBalance)}원
          </p>
          <p className="text-sm text-text-muted mt-1">
            출금가능 {formatAmount(withdrawable)}원
          </p>
        </div>

        <div className="rounded-lg bg-white/40 p-4 shadow-elev-card-soft">
          <p className="text-xs text-text-muted mb-1">총 수익률</p>
          <p className={`text-xl font-bold ${getProfitColor(totalReturn)}`}>
            {formatPercent(totalReturn)}%
          </p>
          <p className="text-sm text-text-muted mt-1">
            평가금액 {formatAmount(evaluationAmount)}원 기준
          </p>
        </div>
      </div>
    </section>
  );
}
