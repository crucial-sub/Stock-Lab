'use client'

import { useEffect, useRef, useState } from 'react'
import type { IChartApi, IPriceLine, ISeriesApi } from 'lightweight-charts'

interface CandleData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface Props {
  candles: CandleData[]
  onChartReady?: () => void
  baselinePrice?: number
}

const PRICE_GRID_STEP = 200
const MIN_GRID_RANGE = PRICE_GRID_STEP * 10
const DEFAULT_VISIBLE_BARS = 100

export default function CandlestickChart({ candles, onChartReady, baselinePrice }: Props) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const priceLinesRef = useRef<IPriceLine[]>([])
  const baselineLineRef = useRef<IPriceLine | null>(null)
  const previousCandleCountRef = useRef(0)
  const [isChartReady, setIsChartReady] = useState(false)

  const clearPriceLines = () => {
    if (!candlestickSeriesRef.current || priceLinesRef.current.length === 0) return
    priceLinesRef.current.forEach((line) => {
      try {
        candlestickSeriesRef.current?.removePriceLine(line)
      } catch {
        // ignore
      }
    })
    priceLinesRef.current = []
  }

  const syncPriceScaleWithStep = (data: CandleData[]) => {
    if (!chartRef.current || !candlestickSeriesRef.current || data.length === 0) {
      return
    }

    const scope = data.slice(-DEFAULT_VISIBLE_BARS)
    const lows = scope.map((c) => c.low)
    const highs = scope.map((c) => c.high)
    const minPrice = Math.min(...lows)
    const maxPrice = Math.max(...highs)
    const lastPrice = scope[scope.length - 1]?.close ?? maxPrice

    const actualSpan = maxPrice - minPrice
    const desiredSpan = Math.max(MIN_GRID_RANGE, actualSpan + PRICE_GRID_STEP * 4)
    const halfSpan = desiredSpan / 2

    let rangeStart = Math.max(0, lastPrice - halfSpan)
    let rangeEnd = lastPrice + halfSpan

    rangeStart = Math.floor(rangeStart / PRICE_GRID_STEP) * PRICE_GRID_STEP
    rangeEnd = Math.ceil(rangeEnd / PRICE_GRID_STEP) * PRICE_GRID_STEP

    // autoScale은 유지하고 price line만 그리기
    clearPriceLines()
    for (let price = rangeStart; price <= rangeEnd; price += PRICE_GRID_STEP) {
      const line = candlestickSeriesRef.current.createPriceLine({
        price,
        color: '#E4E4E7',
        lineWidth: 1,
        lineStyle: 0,
        lineVisible: true,
        axisLabelVisible: true,
        axisLabelColor: '#F4F4F5',
        axisLabelTextColor: '#52525B',
        title: '',
      })
      priceLinesRef.current.push(line)
    }
  }

  const applyBaselineLine = (price?: number) => {
    if (!candlestickSeriesRef.current) return
    if (baselineLineRef.current) {
      candlestickSeriesRef.current.removePriceLine(baselineLineRef.current)
      baselineLineRef.current = null
    }
    if (!price) return
    baselineLineRef.current = candlestickSeriesRef.current.createPriceLine({
      price,
      color: '#EF4444',
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: false,
      title: '',
    })
  }

  const updateTimeRange = (data: CandleData[]) => {
    if (!chartRef.current || data.length === 0) return

    const visibleCandles =
      data.length <= DEFAULT_VISIBLE_BARS ? data : data.slice(-DEFAULT_VISIBLE_BARS)
    const firstVisible = visibleCandles[0]
    const lastVisible = visibleCandles[visibleCandles.length - 1]
    const prevVisible = visibleCandles[visibleCandles.length - 2] ?? lastVisible
    const intervalSeconds = Math.max(60, lastVisible.time - prevVisible.time || 60)
    const padding = intervalSeconds * 2

    requestAnimationFrame(() => {
      if (!chartRef.current) return
      const timeScale = chartRef.current.timeScale()
      if (data.length <= DEFAULT_VISIBLE_BARS) {
        timeScale.fitContent()
      } else {
        timeScale.setVisibleRange({
          from: firstVisible.time as any,
          to: (lastVisible.time + padding) as any,
        })
      }
      timeScale.scrollToRealTime()
    })
  }

  // 차트 초기화
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!chartContainerRef.current) return
    if (chartRef.current) return

    const initChart = () => {
      import('lightweight-charts')
        .then((module) => {
          const { createChart, CandlestickSeries } = module

          if (!chartContainerRef.current) return

          const containerWidth =
            chartContainerRef.current.clientWidth || chartContainerRef.current.offsetWidth || 800
          const containerHeight = 500

          const chart = createChart(chartContainerRef.current, {
            width: containerWidth,
            height: containerHeight,
            layout: {
              background: { color: '#ffffff' },
              textColor: '#71717A',
              fontSize: 12,
            },
            localization: {
              priceFormatter: (price: number) => Math.round(price).toLocaleString('ko-KR'),
            },
            grid: {
              vertLines: {
                color: '#E4E4E7',
                style: 1,
                visible: true,
              },
              horzLines: {
                visible: false,
              },
            },
            crosshair: {
              mode: 1,
              vertLine: {
                color: '#9CA3AF',
                width: 1,
                style: 3,
                labelBackgroundColor: '#1F2937',
              },
              horzLine: {
                color: '#9CA3AF',
                width: 1,
                style: 3,
                labelBackgroundColor: '#1F2937',
              },
            },
            timeScale: {
              timeVisible: true,
              secondsVisible: false,
              borderColor: '#E4E4E7',
              borderVisible: true,
              barSpacing: 10,
              minBarSpacing: 6,
              tickMarkFormatter: (time: any) => {
                const date = new Date(time * 1000)
                const hours = date.getHours().toString().padStart(2, '0')
                const minutes = date.getMinutes().toString().padStart(2, '0')
                return `${hours}:${minutes}`
              },
            },
            rightPriceScale: {
              borderColor: '#E4E4E7',
              borderVisible: true,
              scaleMargins: {
                top: 0.05,
                bottom: 0.05,
              },
              mode: 0,
              autoScale: true,
              minimumWidth: 60,
              visible: true,
              ticksVisible: false,
            },
            leftPriceScale: {
              visible: false,
            },
          })

          const candlestickSeriesInstance = chart.addSeries(CandlestickSeries, {
            upColor: '#EF4444',
            downColor: '#3B82F6',
            borderUpColor: '#EF4444',
            borderDownColor: '#3B82F6',
            wickUpColor: '#EF4444',
            wickDownColor: '#3B82F6',
            borderVisible: true,
            wickVisible: true,
            priceFormat: {
              type: 'price',
              precision: 0,
              minMove: 200,
            },
          })

          chartRef.current = chart
          candlestickSeriesRef.current = candlestickSeriesInstance
          setIsChartReady(true)
          onChartReady?.()

          const handleResize = () => {
            if (!chartContainerRef.current || !chartRef.current) return
            const newWidth =
              chartContainerRef.current.clientWidth || chartContainerRef.current.offsetWidth || 800
            chartRef.current.applyOptions({ width: newWidth })
          }

          window.addEventListener('resize', handleResize)

          return () => {
            window.removeEventListener('resize', handleResize)
          }
        })
        .catch((err) => {
          console.error('차트 라이브러리 로드 실패:', err)
        })
    }

    const timer = setTimeout(initChart, 100)

    return () => {
      clearTimeout(timer)
      if (chartRef.current) {
        clearPriceLines()
        chartRef.current.remove()
        chartRef.current = null
        candlestickSeriesRef.current = null
        baselineLineRef.current = null
        previousCandleCountRef.current = 0
        setIsChartReady(false)
      }
    }
  }, [onChartReady])

  // 데이터 업데이트
  useEffect(() => {
    if (!isChartReady) return
    if (!candlestickSeriesRef.current) return

    if (candles.length === 0) {
      clearPriceLines()
      chartRef.current?.priceScale('right').setAutoScale(true)
      applyBaselineLine(undefined)
      previousCandleCountRef.current = 0
      return
    }

    try {
      const toPositive = (value: number) => (value < 0 ? Math.abs(value) : value)
      const normalized = [...candles]
        .sort((a, b) => a.time - b.time)
        .map((c) => ({
          time: c.time as any,
          open: toPositive(c.open),
          high: toPositive(c.high),
          low: toPositive(c.low),
          close: toPositive(c.close),
          volume: Math.max(0, c.volume),
        }))

      candlestickSeriesRef.current.setData(normalized)
      syncPriceScaleWithStep(normalized)

      // 캔들 개수가 크게 변경되었을 때 (분봉 변경 등) 범위 재조정
      const candleCountChanged =
        previousCandleCountRef.current === 0 ||
        Math.abs(normalized.length - previousCandleCountRef.current) /
          Math.max(1, previousCandleCountRef.current) >
        0.1

      if (candleCountChanged) {
        updateTimeRange(normalized)
      }

      previousCandleCountRef.current = normalized.length

      applyBaselineLine(baselinePrice)
    } catch (err) {
      console.error('차트 업데이트 오류:', err)
    }
  }, [candles, isChartReady, baselinePrice])

  return (
    <div
      ref={chartContainerRef}
      className="w-full relative"
      style={{ height: '500px', minHeight: '500px', position: 'relative' }}
    />
  )
}
