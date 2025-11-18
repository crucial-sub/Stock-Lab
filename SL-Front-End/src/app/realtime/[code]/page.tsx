'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'

// 차트 컴포넌트를 동적으로 로드 (SSR 비활성화)
const CandlestickChart = dynamic(() => import('@/components/CandlestickChart'), {
  ssr: false,
  loading: () => <div className="w-full h-[500px] flex items-center justify-center text-gray-500">차트 로딩 중...</div>
})

const TICK_SERVICE_URL = process.env.NEXT_PUBLIC_TICK_SERVICE_URL || 'http://localhost:8002'

const HISTORY_LIMIT = 20000
const TIMEFRAME_OPTIONS = [
  { label: '1분', value: '1m' },
  { label: '3분', value: '3m' },
  { label: '5분', value: '5m' },
  { label: '10분', value: '10m' },
  { label: '15분', value: '15m' },
  { label: '30분', value: '30m' },
  { label: '60분', value: '60m' },
  { label: '120분', value: '120m' },
  { label: '240분', value: '240m' },
]

const DEFAULT_INTERVAL = '1m'
const MAX_CANDLES = 5000
const MAX_TICKS = 30000

const parseIntervalMinutes = (interval: string) => {
  if (!interval) return 1
  const normalized = interval.toLowerCase().replace('m', '')
  const minutes = parseInt(normalized, 10)
  return Number.isNaN(minutes) ? 1 : minutes
}

const cleanNumber = (value?: string) => {
  if (!value) return null
  const parsed = parseFloat(value.replace(/[+-,]/g, ''))
  return Number.isNaN(parsed) ? null : parsed
}

interface NormalizedTick {
  time: number
  price: number
  volume: number
}

const normalizeTick = (tick: TickData): NormalizedTick | null => {
  if (!tick || !tick.data) return null

  const rawPrice =
    tick.data.price ??
    tick.data.values?.['10']

  const rawVolume =
    tick.data.volume ??
    tick.data.values?.['13']

  const price = cleanNumber(rawPrice ?? '')
  if (!price || Number.isNaN(price)) return null

  const volume = cleanNumber(rawVolume ?? '') ?? 0
  const timestampSource = tick.timestamp || tick.data.timestamp
  const timestamp = timestampSource ? new Date(timestampSource).getTime() : Date.now()
  const time = Math.floor(timestamp / 1000)

  return {
    time,
    price,
    volume
  }
}

const buildCandlesFromTicks = (ticks: NormalizedTick[], intervalMinutes: number): CandleData[] => {
  if (!ticks.length) return []

  const bucketSeconds = Math.max(1, intervalMinutes) * 60
  const map = new Map<number, CandleData>()

  ticks.forEach((tick) => {
    const bucket = Math.floor(tick.time / bucketSeconds) * bucketSeconds
    const target = map.get(bucket)

    if (target) {
      map.set(bucket, {
        time: bucket,
        open: target.open,
        high: Math.max(target.high, tick.price),
        low: Math.min(target.low, tick.price),
        close: tick.price,
        volume: target.volume + tick.volume
      })
    } else {
      map.set(bucket, {
        time: bucket,
        open: tick.price,
        high: tick.price,
        low: tick.price,
        close: tick.price,
        volume: tick.volume
      })
    }
  })

  const sorted = Array.from(map.values()).sort((a, b) => a.time - b.time)
  return sorted.length > MAX_CANDLES ? sorted.slice(sorted.length - MAX_CANDLES) : sorted
}

const appendTickToCandles = (
  candles: CandleData[],
  tick: NormalizedTick,
  intervalMinutes: number
) => {
  if (!intervalMinutes) intervalMinutes = 1
  const bucketSeconds = intervalMinutes * 60
  const bucket = Math.floor(tick.time / bucketSeconds) * bucketSeconds
  const updated = [...candles]
  const targetIndex = updated.findIndex(c => c.time === bucket)

  if (targetIndex >= 0) {
    const existing = updated[targetIndex]
    updated[targetIndex] = {
      time: bucket,
      open: existing.open,
      high: Math.max(existing.high, tick.price),
      low: Math.min(existing.low, tick.price),
      close: tick.price,
      volume: existing.volume + tick.volume
    }
  } else {
    updated.push({
      time: bucket,
      open: tick.price,
      high: tick.price,
      low: tick.price,
      close: tick.price,
      volume: tick.volume
    })
    updated.sort((a, b) => a.time - b.time)
  }

  return updated.length > MAX_CANDLES ? updated.slice(updated.length - MAX_CANDLES) : updated
}

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
    values?: Record<string, string>
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
  const [selectedInterval, setSelectedInterval] = useState<string>(DEFAULT_INTERVAL)
  const [chartReady, setChartReady] = useState(false)
  const ticksRef = useRef<NormalizedTick[]>([])
  const currentIntervalRef = useRef<string>(DEFAULT_INTERVAL)

  // 캔들 데이터 변경 감지
  useEffect(() => {
    console.log(`🔔 캔들 데이터 업데이트: ${candles.length}개`)
    if (candles.length > 0) {
      console.log('첫 번째 캔들:', candles[0])
      console.log('마지막 캔들:', candles[candles.length - 1])
    }
  }, [candles])

  useEffect(() => {
    currentIntervalRef.current = selectedInterval
  }, [selectedInterval])

  // 분봉 변경 시 기존 틱으로 다시 계산
  useEffect(() => {
    if (ticksRef.current.length === 0) return
    const minutes = parseIntervalMinutes(selectedInterval)
    const rebuilt = buildCandlesFromTicks(ticksRef.current, minutes)
    setCandles(rebuilt)
  }, [selectedInterval])

  // 틱 히스토리 로드
  useEffect(() => {
    if (!stockCode) return

    const controller = new AbortController()
    setCandles([])
    ticksRef.current = []

    console.log(`히스토리 요청: ${TICK_SERVICE_URL}/api/stocks/${stockCode}/history?limit=${HISTORY_LIMIT}`)

    fetch(`${TICK_SERVICE_URL}/api/stocks/${stockCode}/history?limit=${HISTORY_LIMIT}`, {
      signal: controller.signal
    })
      .then(res => {
        console.log('히스토리 응답 상태:', res.status, res.ok)
        return res.json()
      })
      .then((data: any) => {
        console.log('히스토리 데이터 타입:', Array.isArray(data) ? 'array' : typeof data, '길이:', Array.isArray(data) ? data.length : 'N/A')

        const ticksArray: TickData[] = Array.isArray(data) ? data : []
        const normalized = ticksArray
          .map(normalizeTick)
          .filter((tick): tick is NormalizedTick => !!tick)

        console.log(`정규화 완료: ${ticksArray.length}개 -> ${normalized.length}개`)

        ticksRef.current = normalized.slice(-MAX_TICKS)

        const minutes = parseIntervalMinutes(currentIntervalRef.current)
        const rebuilt = buildCandlesFromTicks(ticksRef.current, minutes)
        setCandles(rebuilt)

        console.log(`✓ 틱 ${normalized.length}개 로드, ${rebuilt.length}개 캔들 생성`)
      })
      .catch(err => {
        if (err.name === 'AbortError') return
        console.error('틱 히스토리 로드 실패:', err)
      })

    return () => controller.abort()
  }, [stockCode])

  // 차트 준비 콜백 (useCallback으로 안정적인 참조 유지)
  const handleChartReady = useCallback(() => {
    console.log('📊 차트 준비 완료!')
    setChartReady(true)
  }, [])

  // 틱 데이터를 현재 선택된 분봉으로 집계
  const aggregateTickToCandle = useCallback((tick: TickData) => {
    const normalized = normalizeTick(tick)
    if (!normalized) return

    ticksRef.current = [...ticksRef.current, normalized].slice(-MAX_TICKS)

    setCandles(prev => {
      const minutes = parseIntervalMinutes(currentIntervalRef.current)
      const next = appendTickToCandles(prev, normalized, minutes)
      return next
    })
  }, [])

  // 종목 정보 및 WebSocket 연결
  useEffect(() => {

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
  }, [stockCode, aggregateTickToCandle])

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

  const selectedIntervalLabel = TIMEFRAME_OPTIONS.find(option => option.value === selectedInterval)?.label || selectedInterval

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
                <div className={`text-3xl font-bold ${
                  parseFloat(changeRate) > 0 ? 'text-red-600' :
                  parseFloat(changeRate) < 0 ? 'text-blue-600' :
                  'text-gray-900'
                }`}>
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
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-6">
          <div className="px-6 pt-6 pb-4 flex flex-wrap items-center gap-2 border-b border-gray-100">
            {TIMEFRAME_OPTIONS.map(option => {
              const active = option.value === selectedInterval
              return (
                <button
                  key={option.value}
                  onClick={() => setSelectedInterval(option.value)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-full transition ${
                    active
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {option.label}
                </button>
              )
            })}
            <span className="ml-auto text-xs text-gray-400">
              {selectedIntervalLabel} 차트
            </span>
          </div>
          {/* 차트 상단 정보 */}
          <div className="px-6 pt-4 pb-2">
            <div className="text-xs text-gray-400">
              캔들: {candles.length}개 | 차트: {chartReady ? '준비됨' : '로딩 중'}
            </div>
          </div>

          <div className="px-6 pb-6">
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
        </div>

        {/* 설명 */}
        <div className="p-6 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">💡 차트 사용법</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• {selectedIntervalLabel} 캔들스틱 차트로 실시간 가격 변동을 확인할 수 있습니다</li>
            <li>• 마우스 휠로 확대/축소, 드래그로 이동할 수 있습니다</li>
            <li>• 빨간색: 상승, 파란색: 하락</li>
            <li>• 현재 {candles.length}개의 캔들이 표시되고 있습니다</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
