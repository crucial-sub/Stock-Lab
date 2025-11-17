'use client'

import { useEffect, useRef, useState } from 'react'
import type { IChartApi, ISeriesApi } from 'lightweight-charts'

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
}

export default function CandlestickChart({ candles, onChartReady }: Props) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const [isChartReady, setIsChartReady] = useState(false)

  // 차트 초기화
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!chartContainerRef.current) return
    if (chartRef.current) return

    console.log('차트 라이브러리 로딩 중...')

    // 동적으로 lightweight-charts 임포트
    import('lightweight-charts')
      .then((module) => {
        const { createChart, CandlestickSeries, HistogramSeries } = module
        console.log('차트 라이브러리 로드 완료')

        if (!chartContainerRef.current) {
          console.error('chartContainerRef가 없습니다')
          return
        }

        // 컨테이너의 실제 크기 가져오기
        const containerWidth = chartContainerRef.current.offsetWidth || 800
        const containerHeight = 500

        console.log(`차트 생성: ${containerWidth}px x ${containerHeight}px`)

        const chart = createChart(chartContainerRef.current, {
          width: containerWidth,
          height: containerHeight,
          layout: {
            background: { color: '#ffffff' },
            textColor: '#333',
          },
          grid: {
            vertLines: { color: '#f0f0f0' },
            horzLines: { color: '#f0f0f0' },
          },
          timeScale: {
            timeVisible: true,
            secondsVisible: false,
            borderColor: '#e0e0e0',
          },
          rightPriceScale: {
            borderColor: '#e0e0e0',
          },
        })

        console.log('차트 생성 완료')

        // v5 API: addSeries 사용
        const candlestickSeriesInstance = chart.addSeries(CandlestickSeries, {
          upColor: '#ef5350',
          downColor: '#42a5f5',
          borderUpColor: '#ef5350',
          borderDownColor: '#42a5f5',
          wickUpColor: '#ef5350',
          wickDownColor: '#42a5f5',
        })

        const volumeSeriesInstance = chart.addSeries(HistogramSeries, {
          color: '#26a69a',
          priceFormat: {
            type: 'volume',
          },
          priceScaleId: 'volume',
        })

        chart.priceScale('volume').applyOptions({
          scaleMargins: {
            top: 0.8,
            bottom: 0,
          },
        })

        chartRef.current = chart
        candlestickSeriesRef.current = candlestickSeriesInstance
        volumeSeriesRef.current = volumeSeriesInstance

        console.log('차트 초기화 완료!')
        setIsChartReady(true)
        onChartReady?.()

        // 윈도우 리사이즈 처리
        const handleResize = () => {
          if (chartContainerRef.current && chart) {
            const newWidth = chartContainerRef.current.offsetWidth || 800
            chart.applyOptions({ width: newWidth })
            console.log(`차트 리사이즈: ${newWidth}px`)
          }
        }

        window.addEventListener('resize', handleResize)

        // 클린업 함수에서 이벤트 리스너 제거
        return () => {
          window.removeEventListener('resize', handleResize)
        }
      })
      .catch((err) => {
        console.error('차트 라이브러리 로드 실패:', err)
      })

    return () => {
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
        candlestickSeriesRef.current = null
        volumeSeriesRef.current = null
        setIsChartReady(false)
      }
    }
  }, [onChartReady])

  // 데이터 업데이트
  useEffect(() => {
    console.log('데이터 업데이트 시도:', {
      candlesLength: candles.length,
      isChartReady,
      hasCandlestickSeries: !!candlestickSeriesRef.current,
      hasVolumeSeries: !!volumeSeriesRef.current
    })

    if (!isChartReady) {
      console.log('차트가 아직 준비되지 않음')
      return
    }

    if (!candlestickSeriesRef.current || !volumeSeriesRef.current) {
      console.log('시리즈가 아직 준비되지 않음')
      return
    }
    if (candles.length === 0) {
      console.log('캔들 데이터가 없음')
      return
    }

    try {
      const sortedCandles = [...candles].sort((a, b) => a.time - b.time)

      console.log('첫 번째 캔들 샘플:', sortedCandles[0])
      console.log('마지막 캔들 샘플:', sortedCandles[sortedCandles.length - 1])

      const candleData = sortedCandles.map(c => ({
        time: c.time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))

      const volumeData = sortedCandles.map(c => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? '#ef535080' : '#42a5f580',
      }))

      console.log('차트에 데이터 설정 중...')
      candlestickSeriesRef.current.setData(candleData)
      volumeSeriesRef.current.setData(volumeData)

      console.log(`✓ 차트 업데이트 완료: ${sortedCandles.length}개 캔들`)
    } catch (err) {
      console.error('차트 업데이트 오류:', err)
    }
  }, [candles, isChartReady])

  return (
    <div
      ref={chartContainerRef}
      className="w-full relative"
      style={{
        height: '500px',
        minHeight: '500px',
        position: 'relative'
      }}
    />
  )
}
