'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

const TICK_SERVICE_URL = 'http://localhost:8002'

interface StockRank {
  code: string
  name: string
  price: number
  change: number
  changeRate: number
  volume: number
  tradingValue: number
  high: number
  low: number
}

type TabType = 'tradingValue' | 'volume' | 'rising' | 'falling'

const TABS = [
  { id: 'tradingValue' as TabType, label: '거래대금' },
  { id: 'volume' as TabType, label: '거래량' },
  { id: 'rising' as TabType, label: '급상승' },
  { id: 'falling' as TabType, label: '급하락' },
]

export default function RankingPage() {
  const router = useRouter()
  const [selectedTab, setSelectedTab] = useState<TabType>('tradingValue')
  const [stocks, setStocks] = useState<Map<string, StockRank>>(new Map())
  const [connected, setConnected] = useState(false)

  // WebSocket 연결
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8002/ws/realtime')

    ws.onopen = () => {
      console.log('WebSocket 연결됨')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)

        if (message.type === 'TICK') {
          const tick = message.data

          // 원본 Kiwoom 형식
          if (tick.data && tick.data.values) {
            const price = parseFloat(tick.data.values['10']?.replace(/[+-]/g, '') || '0')
            const change = parseFloat(tick.data.values['11'] || '0')
            const changeRate = parseFloat(tick.data.values['12'] || '0')
            const volume = parseFloat(tick.data.values['13'] || '0')
            const high = parseFloat(tick.data.values['17']?.replace(/[+-]/g, '') || '0')
            const low = parseFloat(tick.data.values['18']?.replace(/[+-]/g, '') || '0')

            if (price > 0) {
              setStocks(prev => {
                const newMap = new Map(prev)
                const existing = newMap.get(tick.code)

                newMap.set(tick.code, {
                  code: tick.code,
                  name: existing?.name || tick.code,
                  price,
                  change,
                  changeRate,
                  volume,
                  tradingValue: price * volume,
                  high,
                  low,
                })

                return newMap
              })
            }
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
  }, [])

  // 종목 이름 가져오기
  useEffect(() => {
    fetch(`${TICK_SERVICE_URL}/api/stocks`)
      .then(res => res.json())
      .then((stockList: Array<{code: string, name: string}>) => {
        setStocks(prev => {
          const newMap = new Map(prev)
          stockList.forEach(stock => {
            const existing = newMap.get(stock.code)
            if (existing) {
              newMap.set(stock.code, {
                ...existing,
                name: stock.name
              })
            } else {
              newMap.set(stock.code, {
                code: stock.code,
                name: stock.name,
                price: 0,
                change: 0,
                changeRate: 0,
                volume: 0,
                tradingValue: 0,
                high: 0,
                low: 0,
              })
            }
          })
          return newMap
        })
      })
      .catch(err => console.error('종목 정보 조회 실패:', err))
  }, [])

  // 정렬된 종목 리스트
  const getSortedStocks = (): StockRank[] => {
    const stockArray = Array.from(stocks.values()).filter(s => s.price > 0)

    switch (selectedTab) {
      case 'tradingValue':
        return stockArray.sort((a, b) => b.tradingValue - a.tradingValue)
      case 'volume':
        return stockArray.sort((a, b) => b.volume - a.volume)
      case 'rising':
        return stockArray.sort((a, b) => b.changeRate - a.changeRate)
      case 'falling':
        return stockArray.sort((a, b) => a.changeRate - b.changeRate)
      default:
        return stockArray
    }
  }

  const sortedStocks = getSortedStocks().slice(0, 20)

  const formatNumber = (num: number): string => {
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(1)}억`
    } else if (num >= 10000) {
      return `${(num / 10000).toFixed(0)}만`
    }
    return num.toLocaleString()
  }

  const formatPrice = (price: number): string => {
    return price.toLocaleString() + '원'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">실시간 시세</h1>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-200">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-gray-300'}`} />
              <span className="text-xs font-medium text-gray-700">
                {connected ? '실시간' : '연결 중'}
              </span>
            </div>
          </div>
        </div>

        {/* 탭 */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
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

          {/* 테이블 */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    순위
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    종목명
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    현재가
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    등락률
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {selectedTab === 'tradingValue' ? '거래대금' : '거래량'}
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    차트
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedStocks.map((stock, index) => {
                  const isUp = stock.changeRate > 0
                  const isDown = stock.changeRate < 0
                  const priceColor = isUp ? 'text-red-600' : isDown ? 'text-blue-600' : 'text-gray-900'
                  const bgColor = isUp ? 'bg-red-50' : isDown ? 'bg-blue-50' : 'bg-gray-50'

                  return (
                    <tr
                      key={stock.code}
                      onClick={() => router.push(`/realtime/${stock.code}`)}
                      className="hover:bg-gray-50 cursor-pointer transition"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {index + 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{stock.name}</div>
                        <div className="text-xs text-gray-500">{stock.code}</div>
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${priceColor}`}>
                        {formatPrice(stock.price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${bgColor} ${priceColor}`}>
                          {isUp ? '+' : ''}{stock.changeRate.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                        {selectedTab === 'tradingValue'
                          ? formatNumber(stock.tradingValue)
                          : formatNumber(stock.volume)
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center justify-center gap-1">
                          {/* 간단한 차트바 */}
                          <div className="w-16 h-8 flex items-end gap-0.5">
                            {[...Array(8)].map((_, i) => {
                              const height = Math.random() * 100
                              const barColor = Math.random() > 0.5 ? 'bg-red-400' : 'bg-blue-400'
                              return (
                                <div
                                  key={i}
                                  className={`flex-1 ${barColor} rounded-sm`}
                                  style={{ height: `${height}%` }}
                                />
                              )
                            })}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>

            {sortedStocks.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                실시간 데이터를 기다리는 중...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
