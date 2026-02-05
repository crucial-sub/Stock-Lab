'use client'

import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { useVirtualizer } from '@tanstack/react-virtual'
import { useTickWorker, type TickData } from '@/hooks/useTickWorker'

// TickData는 useTickWorker에서 import

interface StockData {
  code: string
  name?: string
  latest?: TickData
  price?: string
  change_rate?: string
  showFlash?: boolean
  volume?: number
  tradingValue?: number
}

// 테이블 행 높이 상수
const ROW_HEIGHT = 52

type TabType = 'tradingValue' | 'volume' | 'rising' | 'falling'

const TABS = [
  { id: 'tradingValue' as TabType, label: '거래대금' },
  { id: 'volume' as TabType, label: '거래량' },
  { id: 'rising' as TabType, label: '급상승' },
  { id: 'falling' as TabType, label: '급하락' },
]

export default function RealtimePage() {
  const [mode, setMode] = useState<'LIVE' | 'REPLAY' | 'UNKNOWN'>('UNKNOWN')
  const [stocks, setStocks] = useState<StockData[]>([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [selectedTab, setSelectedTab] = useState<TabType>('tradingValue')
  const [previousRanks, setPreviousRanks] = useState<Map<string, number>>(new Map())
  const [rankChanges, setRankChanges] = useState<Map<string, 'up' | 'down' | 'same'>>(new Map())
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const tableContainerRef = useRef<HTMLDivElement>(null)

  // Web Worker를 통한 tick 데이터 배치 처리
  const { sendTick, latestUpdates } = useTickWorker({
    batchInterval: 100,
    enabled: connected,
  })

  // 종목명 매핑
  const stockNames: Record<string, string> = {
    '005930': '삼성전자',
    '000660': 'SK하이닉스',
    '373220': 'LG에너지솔루션',
    '259960': '크래프톤',
    '035420': 'NAVER',
    '035720': '카카오',
    '207940': '삼성바이오로직스',
    '005380': '현대차',
    '051910': 'LG화학',
    '006400': '삼성SDI'
  }

  useEffect(() => {
    // Tick Service에 직접 연결
    const TICK_SERVICE_URL = 'http://localhost:8002'

    // 모드 확인
    fetch(`${TICK_SERVICE_URL}/api/replay/mode`)
      .then(res => res.json())
      .then(data => setMode(data.mode))
      .catch(err => console.error('모드 조회 실패:', err))

    // 종목 리스트 가져오기
    fetch(`${TICK_SERVICE_URL}/api/stocks`)
      .then(res => res.json())
      .then(async (stockList: Array<{code: string, name: string}>) => {
        // 각 종목의 최신 데이터 가져오기
        const stockDataPromises = stockList.map(async (stock) => {
          try {
            const res = await fetch(`${TICK_SERVICE_URL}/api/stocks/${stock.code}/latest`)
            const data = await res.json()
            return {
              code: stock.code,
              name: stock.name,
              latest: data.error ? undefined : data,
              price: data.data?.price,
              change_rate: data.data?.change_rate
            }
          } catch (err) {
            return {
              code: stock.code,
              name: stock.name
            }
          }
        })

        const stockData = await Promise.all(stockDataPromises)
        setStocks(stockData)
      })
      .catch(err => {
        console.error('종목 리스트 조회 실패:', err)
        setError('Tick Service에 연결할 수 없습니다')
      })

    // WebSocket 연결
    const ws = new WebSocket('ws://localhost:8002/ws/realtime')

    ws.onopen = () => {
      console.log('WebSocket 연결됨')
      setConnected(true)
      setError(null)
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'MODE') {
        setMode(message.mode)
      } else if (message.type === 'TICK') {
        // tick 데이터를 Web Worker로 전달하여 배치 처리
        sendTick(message.data as TickData)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error)
      setError('실시간 연결 오류')
      setConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket 연결 종료')
      setConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [])

  // 1초마다 시간 업데이트 (상대 시간 표시를 위해)
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // 가격에 천단위 구분기호 추가
  const formatPrice = (price?: string) => {
    if (!price) return '-'
    return parseInt(price).toLocaleString() + '원'
  }

  // 상대 시간 표시 (토스 스타일 - 간결하게)
  const formatRelativeTime = (timestamp?: string) => {
    if (!timestamp) return '-'

    const now = new Date().getTime()
    const then = new Date(timestamp).getTime()
    const diffSeconds = Math.floor((now - then) / 1000)

    if (diffSeconds < 3) return '방금'
    if (diffSeconds < 60) return `${diffSeconds}초`
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}분`
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}시간`
    return new Date(timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
  }

  // 최근 업데이트 여부 확인 (3초 이내)
  const isRecentUpdate = (timestamp?: string) => {
    if (!timestamp) return false
    const now = new Date().getTime()
    const then = new Date(timestamp).getTime()
    return (now - then) < 3000  // 3초 이내
  }

  // 정렬된 종목 리스트
  const getSortedStocks = (): StockData[] => {
    const stockArray = [...stocks].filter(s => s.price)

    switch (selectedTab) {
      case 'tradingValue':
        return stockArray.sort((a, b) => (b.tradingValue || 0) - (a.tradingValue || 0))
      case 'volume':
        return stockArray.sort((a, b) => (b.volume || 0) - (a.volume || 0))
      case 'rising':
        return stockArray.sort((a, b) => {
          const rateA = parseFloat(a.change_rate || '0')
          const rateB = parseFloat(b.change_rate || '0')
          return rateB - rateA
        })
      case 'falling':
        return stockArray.sort((a, b) => {
          const rateA = parseFloat(a.change_rate || '0')
          const rateB = parseFloat(b.change_rate || '0')
          return rateA - rateB
        })
      default:
        return stockArray
    }
  }

  const sortedStocks = getSortedStocks()

  // Virtual scroll 설정
  const rowVirtualizer = useVirtualizer({
    count: sortedStocks.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 5,
  })

  // Web Worker로부터 배치 업데이트 수신 시 stocks 상태 업데이트
  useEffect(() => {
    if (Object.keys(latestUpdates).length === 0) return

    setStocks(prev => prev.map(stock => {
      const update = latestUpdates[stock.code]
      if (!update) return stock

      const prevRate = stock.change_rate
      const newRate = update.change_rate
      const hasChanged = prevRate && newRate && prevRate !== newRate

      // 등락률 변경 시 flash 효과
      if (hasChanged) {
        setTimeout(() => {
          setStocks(prevStocks => prevStocks.map(s =>
            s.code === stock.code ? { ...s, showFlash: false } : s
          ))
        }, 1500)
      }

      return {
        ...stock,
        price: update.price,
        change_rate: update.change_rate,
        volume: update.volume,
        tradingValue: update.tradingValue,
        showFlash: Boolean(hasChanged),
      }
    }))
  }, [latestUpdates])

  // 초기 로딩 완료 감지
  useEffect(() => {
    if (stocks.length > 0 && isInitialLoad) {
      // 3초 후 초기 로딩 완료로 간주
      const timer = setTimeout(() => {
        setIsInitialLoad(false)
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [stocks.length, isInitialLoad])

  // 순위 변동 추적 (가상 스크롤과 호환되는 방식)
  useEffect(() => {
    if (isInitialLoad) return

    const newRanks = new Map<string, number>()
    const changes = new Map<string, 'up' | 'down' | 'same'>()

    sortedStocks.forEach((stock, index) => {
      const currentRank = index + 1
      const previousRank = previousRanks.get(stock.code)

      newRanks.set(stock.code, currentRank)

      if (previousRank !== undefined) {
        if (currentRank < previousRank) {
          changes.set(stock.code, 'up')
        } else if (currentRank > previousRank) {
          changes.set(stock.code, 'down')
        } else {
          changes.set(stock.code, 'same')
        }
      }
    })

    setPreviousRanks(newRanks)
    setRankChanges(changes)

    // 1.5초 후 순위 변동 표시 초기화
    const timer = setTimeout(() => {
      setRankChanges(new Map())
    }, 1500)

    return () => clearTimeout(timer)
  }, [sortedStocks.map(s => s.code + s.change_rate).join(','), isInitialLoad])

  const formatNumber = (num: number): string => {
    if (num >= 1000000000000) {
      // 1조 이상
      const jo = Math.floor(num / 1000000000000)
      const eok = Math.floor((num % 1000000000000) / 100000000)
      return eok > 0 ? `${jo}조 ${eok}억` : `${jo}조`
    } else if (num >= 100000000) {
      // 1억 이상
      return `${Math.floor(num / 100000000)}억`
    } else if (num >= 10000) {
      // 1만 이상
      return `${Math.floor(num / 10000)}만`
    }
    return num.toLocaleString()
  }

  // 매수/매도 강도 바 렌더링 (토스 스타일)
  const renderStrengthBar = (strength?: string) => {
    if (!strength) return <div className="text-xs text-gray-400">-</div>

    const value = parseFloat(strength)
    if (isNaN(value)) return <div className="text-xs text-gray-400">-</div>

    // -100 ~ +100 범위를 0~100%로 정규화
    const buyPercent = Math.max(0, Math.min(100, ((value + 100) / 2)))
    const sellPercent = 100 - buyPercent

    return (
      <div className="flex items-center gap-2 w-full justify-center">
        {/* 매수 (파랑) - 왼쪽 */}
        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden flex justify-end">
          <div
            className="h-full bg-blue-500 transition-all duration-500 ease-out"
            style={{ width: `${buyPercent}%` }}
          />
        </div>

        {/* 수치 */}
        <div className="text-xs font-medium text-gray-500 w-8 text-center">
          {Math.abs(value).toFixed(0)}
        </div>

        {/* 매도 (빨강) - 오른쪽 */}
        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden flex">
          <div
            className="h-full bg-red-500 transition-all duration-500 ease-out"
            style={{ width: `${sellPercent}%` }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-3">실시간 시세</h1>

          <div className="flex gap-3 items-center">
            {/* 연결 상태 */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-200">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-blue-500' : 'bg-gray-300'}`} />
              <span className="text-xs font-medium text-gray-700">
                {connected ? '실시간' : '연결 중'}
              </span>
            </div>

            {/* 모드 */}
            <div className="px-3 py-1.5 bg-white rounded-lg border border-gray-200">
              {mode === 'LIVE' && (
                <span className="text-xs font-medium text-red-600">LIVE</span>
              )}
              {mode === 'REPLAY' && (
                <span className="text-xs font-medium text-blue-600">REPLAY</span>
              )}
              {mode === 'UNKNOWN' && (
                <span className="text-xs font-medium text-gray-500">확인 중</span>
              )}
            </div>

            {/* 종목 수 */}
            <div className="text-xs text-gray-500">
              {stocks.length}개 종목
            </div>
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              ⚠️ {error}
              <div className="mt-2 text-sm">
                Tick Service가 실행 중인지 확인하세요: <code>docker logs tick-service -f</code>
              </div>
            </div>
          )}
        </div>

        {/* 종목 리스트 */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {/* 탭 */}
          <div className="border-b border-gray-200">
            <div className="flex">
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id)}
                  className={`flex-1 px-6 py-4 text-sm font-medium transition ${
                    selectedTab === tab.id
                      ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* 테이블 헤더 */}
          <div className="grid grid-cols-[80px_96px_128px_112px_96px_96px_192px] bg-white border-b border-gray-100">
            <div className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">
              순위
            </div>
            <div className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">
              종목
            </div>
            <div className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">
              이름
            </div>
            <div className="px-4 py-2.5 text-right text-xs font-medium text-gray-500">
              현재가
            </div>
            <div className="px-4 py-2.5 text-right text-xs font-medium text-gray-500">
              등락률
            </div>
            <div className="px-4 py-2.5 text-right text-xs font-medium text-gray-500">
              {selectedTab === 'tradingValue' ? '거래대금' : '거래량'}
            </div>
            <div className="px-4 py-2.5 text-center text-xs font-medium text-gray-500">
              체결강도
            </div>
          </div>

          {/* 가상화된 테이블 바디 */}
          {sortedStocks.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              데이터 로딩 중...
            </div>
          ) : (
            <div
              ref={tableContainerRef}
              className="overflow-auto"
              style={{ height: 'calc(100vh - 380px)', minHeight: '400px' }}
            >
              <div
                style={{
                  height: `${rowVirtualizer.getTotalSize()}px`,
                  width: '100%',
                  position: 'relative',
                }}
              >
                {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                  const stock = sortedStocks[virtualRow.index]
                  const changeRate = stock.change_rate ? parseFloat(stock.change_rate) : 0
                  const isPositive = changeRate > 0
                  const isNegative = changeRate < 0
                  const rankChange = rankChanges.get(stock.code)

                  return (
                    <div
                      key={stock.code}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: `${virtualRow.size}px`,
                        transform: `translateY(${virtualRow.start}px)`,
                      }}
                    >
                      <div
                        className="grid grid-cols-[80px_96px_128px_112px_96px_96px_192px] h-full items-center border-b border-gray-50 hover:bg-gray-50/50 cursor-pointer"
                        onClick={() => window.location.href = `/realtime/${stock.code}`}
                      >
                        <div className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                          <div className="flex items-center gap-1.5">
                            <span className="w-6 text-center">{virtualRow.index + 1}</span>
                            {rankChange === 'up' && (
                              <span className="text-red-500 text-[10px]">▲</span>
                            )}
                            {rankChange === 'down' && (
                              <span className="text-blue-500 text-[10px]">▼</span>
                            )}
                          </div>
                        </div>
                        <div className="px-4 py-3 whitespace-nowrap text-xs font-mono text-gray-500">
                          {stock.code}
                        </div>
                        <div className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                          <Link
                            href={`/realtime/${stock.code}`}
                            className="text-gray-900 hover:text-blue-600 hover:underline transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {stock.name}
                          </Link>
                        </div>
                        <div className="px-4 py-3 whitespace-nowrap text-sm text-right font-semibold text-gray-900 tabular-nums">
                          {formatPrice(stock.price)}
                        </div>
                        <div className="px-4 py-3 whitespace-nowrap text-sm text-right">
                          <span className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-300 min-w-[60px] ${
                            stock.showFlash
                              ? isPositive
                                ? 'bg-red-200 text-red-700'
                                : 'bg-blue-200 text-blue-700'
                              : isPositive
                                ? 'bg-red-50 text-red-600'
                                : isNegative
                                  ? 'bg-blue-50 text-blue-600'
                                  : 'bg-gray-50 text-gray-600'
                          }`}>
                            {isPositive ? '+' : ''}{changeRate.toFixed(2)}%
                          </span>
                        </div>
                        <div className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900 tabular-nums">
                          {selectedTab === 'tradingValue'
                            ? formatNumber(stock.tradingValue || 0)
                            : formatNumber(stock.volume || 0)
                          }
                        </div>
                        <div className="px-4 py-3 whitespace-nowrap">
                          {renderStrengthBar(stock.latest?.data.strength)}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* 종목 수 표시 */}
          {sortedStocks.length > 0 && (
            <div className="px-6 py-3 border-t border-gray-100 text-center text-sm text-gray-500">
              총 {sortedStocks.length}개 종목 (스크롤하여 더 보기)
            </div>
          )}
        </div>

        {/* 설명 */}
        <div className="mt-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">💡 사용 가이드</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>LIVE 모드</strong>: 평일 거래 시간(08:20~18:00)에 실시간 데이터 수집</li>
            <li>• <strong>REPLAY 모드</strong>: 주말/장 마감 후 과거 데이터 재생 (10배속)</li>
            <li>• WebSocket으로 실시간 업데이트 - 데이터가 들어오면 자동으로 갱신됩니다</li>
            <li>• Tick Service 상태 확인: <code className="bg-blue-100 px-2 py-1 rounded">docker logs tick-service -f</code></li>
          </ul>
        </div>
      </div>
    </div>
  )
}
