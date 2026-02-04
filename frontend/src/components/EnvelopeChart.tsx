import { useState, useEffect, useRef } from 'react'
import Plot from 'react-plotly.js'
import { Download, ZoomIn, ZoomOut, RefreshCw, Maximize2 } from 'lucide-react'

export interface EnvelopeData {
  xAxis: string
  yAxis: string
  xData: number[]
  yData: number[]
  xLabel: string
  yLabel: string
  title: string
}

export interface EnvelopeChartProps {
  data: EnvelopeData
  onDataChange?: (data: EnvelopeData) => void
  showGrid?: boolean
  showLegend?: boolean
}

export function EnvelopeChart({
  data,
  onDataChange,
  showGrid = true,
  showLegend = true,
}: EnvelopeChartProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const chartRef = useRef<HTMLDivElement>(null)

  const plotData = [
    {
      x: data.xData,
      y: data.yData,
      type: 'scatter',
      mode: 'lines+markers',
      name: '约束包络',
      line: {
        color: '#3b82f6',
        width: 3,
      },
      marker: {
        size: 8,
        color: '#3b82f6',
      },
    },
  ]

  const layout = {
    title: {
      text: data.title,
      font: {
        size: 18,
        family: 'Arial, sans-serif',
      },
    },
    xaxis: {
      title: {
        text: data.xLabel,
        font: {
          size: 14,
        },
      },
      grid: {
        show: showGrid,
        color: '#e5e7eb',
        width: 1,
      },
      zeroline: false,
    },
    yaxis: {
      title: {
        text: data.yLabel,
        font: {
          size: 14,
        },
      },
      grid: {
        show: showGrid,
        color: '#e5e7eb',
        width: 1,
      },
      zeroline: false,
    },
    showlegend: showLegend,
    hovermode: 'closest',
    autosize: true,
    margin: {
      l: 60,
      r: 40,
      b: 60,
      t: 60,
    },
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtons: [
      ['toImage'],
      ['zoom2d'],
      ['select2d'],
    ],
  }

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
    }, 1000)
  }

  const handleZoomIn = () => {
    const plot = chartRef.current?.querySelector('.plotly')
    if (plot) {
      const plotInstance = (plot as any)._plotly
      if (plotInstance) {
        plotInstance.relayout({
          'xaxis.range': [
            data.xData[0] * 0.9,
            data.xData[data.xData.length - 1] * 1.1,
          ],
          'yaxis.range': [
            data.yData[0] * 0.9,
            data.yData[data.yData.length - 1] * 1.1,
          ],
        })
      }
    }
  }

  const handleZoomOut = () => {
    const plot = chartRef.current?.querySelector('.plotly')
    if (plot) {
      const plotInstance = (plot as any)._plotly
      if (plotInstance) {
        plotInstance.relayout({
          'xaxis.autorange': true,
          'yaxis.autorange': true,
        })
      }
    }
  }

  const handleDownload = () => {
    const plot = chartRef.current?.querySelector('.plotly')
    if (plot) {
      const plotInstance = (plot as any)._plotly
      if (plotInstance) {
        plotInstance.downloadImage({
          format: 'png',
          width: 1920,
          height: 1080,
          filename: `envelope_${Date.now()}.png`,
        })
      }
    }
  }

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      chartRef.current?.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
    setIsFullscreen(!isFullscreen)
  }

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  return (
    <div className={`w-full ${isFullscreen ? 'fixed inset-0 z-50 bg-background' : ''}`}>
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-xl font-semibold">{data.title}</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="p-2 rounded-md hover:bg-accent"
            title="刷新"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleZoomIn}
            className="p-2 rounded-md hover:bg-accent"
            title="放大"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 rounded-md hover:bg-accent"
            title="缩小"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <button
            onClick={handleDownload}
            className="p-2 rounded-md hover:bg-accent"
            title="下载"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-md hover:bg-accent"
            title="全屏"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div ref={chartRef} className="w-full h-[calc(100vh-200px)]">
        <Plot
          data={plotData}
          layout={layout}
          config={config}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      <div className="flex items-center justify-between p-4 border-t">
        <div className="text-sm text-muted-foreground">
          <span>X轴: {data.xLabel} ({data.xAxis})</span>
          <span className="mx-4">|</span>
          <span>Y轴: {data.yLabel} ({data.yAxis})</span>
        </div>
        <div className="text-sm text-muted-foreground">
          <span>数据点: {data.xData.length}</span>
        </div>
      </div>
    </div>
  )
}
