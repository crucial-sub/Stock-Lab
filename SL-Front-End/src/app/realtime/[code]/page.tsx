'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'

// 차트 컴포넌트를 동적으로 로드 (SSR 비활성화)
const CandlestickChart = dynamic(() => import('@/components/CandlestickChart'), {
  ssr: false,
  loading: () => <div className="w-full h-[500px] flex items-center justify-center text-gray-500">차트 로딩 중...</div>
})

interface TickData {
  timestamp: string
  client: string
  code: string
  data: {
    item: string
    price: string
    open: string
    high: string
    low: string
    change: string
    change_rate: string
    volume: string
    timestamp: string
    strength?: string
    net_buy_volume?: string
  }
}

interface CandleData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export default function StockDetailPage() {
  const params = useParams()
  const router = useRouter()
  const stockCode = params.code as string

  const [stockName, setStockName] = useState<string>('')
  const [currentPrice, setCurrentPrice] = useState<string>('-')
  const [changeRate, setChangeRate] = useState<string>('0')
  const [connected, setConnected] = useState(false)
  const [candles, setCandles] = useState<CandleData[]>([])
  const [chartReady, setChartReady] = useState(false)

  // 캔들 데이터 변경 감지
  useEffect(() => {
    console.log(`🔔 캔들 데이터 업데이트: ${candles.length}개`)
    if (candles.length > 0) {
      console.log('첫 번째 캔들:', candles[0])
      console.log('마지막 캔들:', candles[candles.length - 1])
    }
  }, [candles])

  // 차트 준비 콜백 (useCallback으로 안정적인 참조 유지)
  const handleChartReady = useCallback(() => {
    console.log('📊 차트 준비 완료!')
    setChartReady(true)
  }, [])

  // 틱 데이터를 1분봉으로 집계
  const aggregateTickToCandle = (tick: TickData) => {
    try {
      const price = parseFloat(tick.data.price)
      const volume = parseFloat(tick.data.volume) || 0

      if (isNaN(price) || price === 0) {
        console.log('잘못된 가격 데이터:', tick.data.price)
        return
      }

      const tickTime = new Date(tick.timestamp).getTime()
      // 1분 단위로 반올림 (초 단위 제거)
      const candleTime = Math.floor(tickTime / 60000) * 60

      setCandles(prev => {
        const candleMap = new Map(prev.map(c => [c.time, c]))
        const existing = candleMap.get(candleTime)

        if (existing) {
          // 기존 캔들 업데이트
          candleMap.set(candleTime, {
            time: candleTime,
            open: existing.open,
            high: Math.max(existing.high, price),
            low: Math.min(existing.low, price),
            close: price,
            volume: existing.volume + volume
          })
        } else {
          // 새 캔들 생성
          candleMap.set(candleTime, {
            time: candleTime,
            open: price,
            high: price,
            low: price,
            close: price,
            volume: volume
          })
          console.log(`📈 새 캔들 생성: time=${candleTime}, price=${price}`)
        }

        const result = Array.from(candleMap.values())
        if (result.length !== prev.length) {
          console.log(`캔들 개수 변경: ${prev.length} → ${result.length}`)
        }
        return result
      })
    } catch (err) {
      console.error('캔들 집계 오류:', err)
    }
  }

  // 종목 정보 및 WebSocket 연결
  useEffect(() => {
    const TICK_SERVICE_URL = 'http://localhost:8002'

    console.log(`종목 ${stockCode} 데이터 로드 시작`)

    // 종목 정보 가져오기
    fetch(`${TICK_SERVICE_URL}/api/stocks`)
      .then(res => res.json())
      .then((stocks: Array<{code: string, name: string}>) => {
        const stock = stocks.find(s => s.code === stockCode)
        if (stock) {
          setStockName(stock.name)
          console.log(`종목명: ${stock.name}`)
        }
      })
      .catch(err => console.error('종목 정보 조회 실패:', err))

    // 최신 데이터 가져오기
    fetch(`${TICK_SERVICE_URL}/api/stocks/${stockCode}/latest`)
      .then(res => res.json())
      .then((tick: TickData) => {
        if (tick && tick.data && tick.data.price) {
          setCurrentPrice(tick.data.price)
          setChangeRate(tick.data.change_rate)
          console.log(`최신 가격: ${tick.data.price}`)
        }
      })
      .catch(err => console.error('최신 데이터 조회 실패:', err))

    // 과거 데이터 로드
    fetch(`${TICK_SERVICE_URL}/api/stocks/${stockCode}/history?limit=500`)
      .then(res => res.json())
      .then((data: any) => {
        // 배열인지 확인
        const ticks = Array.isArray(data) ? data : []
        console.log(`📊 과거 데이터 받음: ${ticks.length}개 틱`)

        if (ticks.length > 0) {
          console.log('첫 번째 틱 샘플:', ticks[0])
        }

        let processedCount = 0
        ticks.forEach(tick => {
          // 데이터 형식 확인
          if (tick.data && tick.data.values) {
            // 원본 Kiwoom 형식
            const price = tick.data.values['10']?.replace('+', '') || '0'
            const volume = tick.data.values['13'] || '0'

            const transformedTick: TickData = {
              timestamp: tick.timestamp,
              client: tick.client,
              code: tick.code,
              data: {
                item: tick.code,
                price: price,
                open: tick.data.values['16']?.replace('+', '') || price,
                high: tick.data.values['17']?.replace('+', '') || price,
                low: tick.data.values['18']?.replace('+', '') || price,
                change: tick.data.values['11'] || '0',
                change_rate: tick.data.values['12'] || '0',
                volume: volume,
                timestamp: tick.data.values['20'] || '',
                strength: tick.data.values['30'],
                net_buy_volume: tick.data.values['26'],
              }
            }
            aggregateTickToCandle(transformedTick)
            processedCount++
          } else if (tick.data && tick.data.price) {
            // 이미 변환된 형식
            aggregateTickToCandle(tick)
            processedCount++
          }
        })

        console.log(`✓ ${processedCount}개 틱 처리 완료`)
      })
      .catch(err => console.error('과거 데이터 로드 실패:', err))

    // WebSocket 연결
    const ws = new WebSocket('ws://localhost:8002/ws/realtime')

    ws.onopen = () => {
      console.log('WebSocket 연결됨')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)

        if (message.type === 'TICK' && message.data.code === stockCode) {
          const tick: TickData = message.data

          // 현재가 업데이트
          if (tick.data.price) {
            setCurrentPrice(tick.data.price)
            setChangeRate(tick.data.change_rate)

            // 캔들 집계
            aggregateTickToCandle(tick)
          }
        }
      } catch (err) {
        console.error('WebSocket 메시지 파싱 오류:', err)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error)
      setConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket 연결 종료')
      setConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [stockCode])

  const formatPrice = (price: string) => {
    if (price === '-') return '-'
    const num = parseInt(price)
    if (isNaN(num)) return '-'
    return num.toLocaleString() + '원'
  }

  const formatChangeRate = (rate: string) => {
    const num = parseFloat(rate)
    if (isNaN(num)) return <span className="text-gray-600">-</span>
    const color = num > 0 ? 'text-red-600' : num < 0 ? 'text-blue-600' : 'text-gray-600'
    const sign = num > 0 ? '+' : ''
    return <span className={color}>{sign}{num.toFixed(2)}%</span>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* 헤더 */}
        <div className="mb-6">
          <button
            onClick={() => router.push('/realtime')}
            className="mb-4 text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
          >
            ← 목록으로
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {stockName || stockCode}
                {stockName && <span className="ml-3 text-sm text-gray-500 font-normal">{stockCode}</span>}
              </h1>
              <div className="mt-2 flex items-center gap-4">
                <div className="text-3xl font-bold text-gray-900">
                  {formatPrice(currentPrice)}
                </div>
                <div className="text-xl">
                  {formatChangeRate(changeRate)}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-200">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-blue-500' : 'bg-gray-300'}`} />
              <span className="text-xs font-medium text-gray-700">
                {connected ? '실시간' : '연결 중'}
              </span>
            </div>
          </div>
        </div>

        {/* 차트 */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">1분봉 차트</h2>
            <div className="text-sm text-gray-600">
              캔들: {candles.length}개 | 차트 준비: {chartReady ? '✓' : '⏳'}
            </div>
          </div>
          <CandlestickChart
            candles={candles}
            onChartReady={handleChartReady}
          />
          {candles.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              데이터 로딩 중... (캔들: {candles.length}개)
            </div>
          )}
        </div>

        {/* 설명 */}
        <div className="p-6 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">💡 차트 사용법</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• 1분봉 캔들스틱 차트로 실시간 가격 변동을 확인할 수 있습니다</li>
            <li>• 마우스 휠로 확대/축소, 드래그로 이동할 수 있습니다</li>
            <li>• 빨간색: 상승, 파란색: 하락</li>
            <li>• 하단 히스토그램은 거래량을 나타냅니다</li>
            <li>• 현재 {candles.length}개의 캔들이 표시되고 있습니다</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
