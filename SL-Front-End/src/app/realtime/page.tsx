'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface TickData {
  timestamp: string
  client: string
  code: string
  data: {
    item: string
    price: string
    change: string
    change_rate: string
    volume: string
    timestamp: string
    strength?: string  // 체결강도 (-100~+100)
    net_buy_volume?: string  // 순매수량
  }
}

interface StockData {
  code: string
  name?: string
  latest?: TickData
  price?: string
  change_rate?: string
  showFlash?: boolean
}

export default function RealtimePage() {
  const [mode, setMode] = useState<'LIVE' | 'REPLAY' | 'UNKNOWN'>('UNKNOWN')
  const [stocks, setStocks] = useState<StockData[]>([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(new Date())

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
        const tick: TickData = message.data

        // 해당 종목 데이터 업데이트
        setStocks(prev => prev.map(stock => {
          if (stock.code === tick.code) {
            const prevRate = stock.change_rate
            const newRate = tick.data.change_rate
            const hasChanged = prevRate && newRate && prevRate !== newRate

            // 등락률 변경 시 flash 효과
            if (hasChanged) {
              // 1.5초 후 flash 제거
              setTimeout(() => {
                setStocks(prev => prev.map(s =>
                  s.code === tick.code ? { ...s, showFlash: false } : s
                ))
              }, 1500)
            }

            return {
              ...stock,
              latest: tick,
              price: tick.data.price,
              change_rate: newRate,
              showFlash: hasChanged
            }
          }
          return stock
        }))
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

  // 등락률 포맷팅
  const formatChangeRate = (rate?: string) => {
    if (!rate) return '-'
    const num = parseFloat(rate)
    const color = num > 0 ? 'text-red-600' : num < 0 ? 'text-blue-600' : 'text-gray-600'
    const sign = num > 0 ? '+' : ''
    return <span className={color}>{sign}{num.toFixed(2)}%</span>
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
          <table className="min-w-full">
            <thead className="bg-white border-b border-gray-100">
              <tr>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">
                  종목
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">
                  이름
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500">
                  현재가
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500">
                  등락률
                </th>
                <th className="px-4 py-2.5 text-center text-xs font-medium text-gray-500 w-48">
                  체결강도
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500">
                  거래량
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-50">
              {stocks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    데이터 로딩 중...
                  </td>
                </tr>
              ) : (
                stocks.map((stock) => {
                  const changeRate = stock.change_rate ? parseFloat(stock.change_rate) : 0
                  const isPositive = changeRate > 0

                  return (
                    <tr
                      key={stock.code}
                      className="hover:bg-gray-50/50 transition-colors duration-200"
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-xs font-mono text-gray-500">
                        {stock.code}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                        <Link
                          href={`/realtime/${stock.code}`}
                          className="text-gray-900 hover:text-blue-600 hover:underline transition-colors"
                        >
                          {stock.name}
                        </Link>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-semibold text-gray-900">
                        {formatPrice(stock.price)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                        <span className={`inline-block px-2.5 py-1 rounded-md transition-colors duration-500 ${
                          stock.showFlash
                            ? isPositive
                              ? 'bg-red-100'
                              : 'bg-blue-100'
                            : ''
                        }`}>
                          {formatChangeRate(stock.change_rate)}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {renderStrengthBar(stock.latest?.data.strength)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-gray-600">
                        {stock.latest?.data.volume ? parseInt(stock.latest.data.volume).toLocaleString() : '-'}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
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
