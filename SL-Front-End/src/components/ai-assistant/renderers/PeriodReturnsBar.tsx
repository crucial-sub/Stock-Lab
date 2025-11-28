/**
 * AI 어시스턴트용 기간별 수익률 막대 차트 컴포넌트
 */

interface PeriodReturn {
  label: string;
  value: number;
}

interface PeriodReturnsBarProps {
  periodReturns: PeriodReturn[];
}

export function PeriodReturnsBar({ periodReturns }: PeriodReturnsBarProps) {
  // 데이터가 없는 경우 빈 상태 표시
  if (!periodReturns || periodReturns.length === 0) {
    return (
      <div className="w-full rounded-lg mb-10">
        <h3 className="text-[1.25rem] font-semibold mb-6">📊 수익률 (%)</h3>
        <div className="text-center text-gray-500 py-10">
          기간별 수익률 데이터가 없습니다.
        </div>
      </div>
    );
  }

  // 최대값 계산 (절댓값 기준)
  const maxAbsValue = Math.max(...periodReturns.map(p => Math.abs(p.value)));

  // 막대 높이 계산 (최대 60px)
  const getBarHeight = (value: number) => {
    if (maxAbsValue === 0) return 0;
    return (Math.abs(value) / maxAbsValue) * 60;
  };

  return (
    <div className="w-full rounded-lg mb-10">
      <h3 className="text-[1.25rem] font-semibold mb-6">📊 수익률 (%)</h3>

      {/* 차트 영역 */}
      <div className="relative" style={{ height: '200px' }}>
        {/* 중앙 기준선 (0% 라인) - 전체 너비에 걸쳐서 */}
        <div className="absolute w-full h-[1px] bg-gray-300" style={{ top: '50%' }} />

        {/* 막대들을 담는 컨테이너 */}
        <div className="flex items-stretch justify-between gap-3 h-full">
          {periodReturns.map((item, index) => {
            const isPositive = item.value >= 0;
            const barHeight = getBarHeight(item.value);
            const bgColor = isPositive ? 'bg-red-500' : 'bg-blue-500';
            const textColor = isPositive ? 'text-red-500' : 'text-blue-500';

            return (
              <div key={index} className="flex-1 flex flex-col items-center relative">
                {/* 상단 영역 (양수 막대와 수치) */}
                <div className="flex-1 flex flex-col items-center justify-end">
                  {isPositive && (
                    <>
                      <div className={`text-xs font-bold mb-1 ${textColor}`}>
                        +{item.value.toFixed(2)}%
                      </div>
                      <div
                        className={`w-10 ${bgColor} rounded-t-sm`}
                        style={{ height: `${barHeight}px` }}
                      />
                    </>
                  )}
                </div>

                {/* 하단 영역 (음수 막대와 수치) */}
                <div className="flex-1 flex flex-col items-center justify-start">
                  {!isPositive && item.value !== 0 && (
                    <>
                      <div
                        className={`w-10 ${bgColor} rounded-b-sm`}
                        style={{ height: `${barHeight}px` }}
                      />
                      <div className={`text-xs font-bold mt-1 ${textColor}`}>
                        {item.value.toFixed(2)}%
                      </div>
                    </>
                  )}
                </div>

                {/* 라벨 (하단에 위치) */}
                <div className="absolute bottom-0 text-xs text-gray-600 whitespace-nowrap">
                  {item.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}