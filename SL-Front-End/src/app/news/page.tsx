import type { NextPage } from "next";

export default function NewsPage() {
	return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm text-text-muted">실시간 뉴스 피드</p>
        <h1 className="text-4xl font-semibold text-text-strong">오늘의 뉴스</h1>
        <p className="text-base text-text-body">
          최신 시장 뉴스와 종목 관련 기사를 한 곳에서 확인하세요.
        </p>
      </header>

      <div className="rounded-xl border border-border-subtle bg-white p-6 text-center text-text-muted">
        <p className="text-lg font-medium">
          뉴스 데이터 연동 전입니다. 추후 API 연결 후 실제 기사가 노출될 예정입니다.
        </p>
      </div>
    </section>
  );
}