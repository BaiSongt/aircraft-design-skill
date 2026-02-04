import { useState, useEffect } from 'react'
import { ModeToggle } from '@/components/ModeToggle'
import { ChatInterface } from '@/components/ChatInterface'
import { ModelSelector } from '@/components/ModelSelector'
import { EnvelopeChart } from '@/components/EnvelopeChart'
import { Model3DViewer } from '@/components/Model3DViewer'
import { ResultTable } from '@/components/ResultTable'
import { Settings } from '@/pages/Settings'
import { History } from '@/pages/History'
import { useAIProvider } from '@/hooks/useAIProvider'
import { useWebSocket } from '@/hooks/useWebSocket'
import { MessageSquare, Home, Settings as SettingsIcon, History as HistoryIcon, BarChart3, Box } from 'lucide-react'

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  metadata?: {
    skill?: string
    parameters?: Record<string, any>
    result?: any
    error?: string
  }
}

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved === 'true'
  })

  const [currentView, setCurrentView] = useState<'chat' | 'envelope' | '3d' | 'settings' | 'history'>('chat')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [envelopeData, setEnvelopeData] = useState<any>(null)
  const [modelData, setModelData] = useState<any>(null)
  const [results, setResults] = useState<any[]>([])
  const [isMobile, setIsMobile] = useState(false)

  const { provider, setAIProvider } = useAIProvider()
  const { isConnected, sendMessage } = useWebSocket()

  useEffect(() => {
    localStorage.setItem('darkMode', String(darkMode))
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768)
    }

    window.addEventListener('resize', handleResize)
    handleResize()

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  useEffect(() => {
    const savedHistory = localStorage.getItem('history')
    if (savedHistory) {
      const history = JSON.parse(savedHistory)
      setResults(history)
    }
  }, [])

  const handleSendMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const fullMessage: ChatMessage = {
      ...message,
      id: Date.now().toString(),
      timestamp: Date.now(),
    }

    setMessages(prev => [...prev, fullMessage])

    const history = JSON.parse(localStorage.getItem('history') || '[]')
    history.push(fullMessage)
    localStorage.setItem('history', JSON.stringify(history))
  }

  const handleEnvelopeChange = (data: any) => {
    setEnvelopeData(data)
  }

  const handleModelChange = (data: any) => {
    setModelData(data)
  }

  const handleResultClick = (row: any) => {
    console.log('Result clicked:', row)
  }

  const handleResultDelete = (row: any) => {
    const newResults = results.filter(r => r.id !== row.id)
    setResults(newResults)
    localStorage.setItem('results', JSON.stringify(newResults))
  }

  const handleResultExport = () => {
    const dataStr = JSON.stringify(results, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `results_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const navItems = [
    { id: 'chat', label: '聊天', icon: MessageSquare },
    { id: 'envelope', label: '包络图', icon: BarChart3 },
    { id: '3d', label: '3D模型', icon: Box },
    { id: 'settings', label: '设置', icon: SettingsIcon },
    { id: 'history', label: '历史', icon: HistoryIcon },
  ]

  return (
    <div className={`min-h-screen bg-background text-foreground ${darkMode ? 'dark' : ''}`}>
      <header className="border-b bg-card sticky top-0 z-40">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <Home className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold hidden md:block">
                飞机设计系统
              </h1>
            </div>

            <div className="flex items-center gap-4">
              {isMobile ? (
                <select
                  value={currentView}
                  onChange={(e) => setCurrentView(e.target.value as any)}
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                >
                  {navItems.map(item => (
                    <option key={item.id} value={item.id}>
                      {item.label}
                    </option>
                  ))}
                </select>
              ) : (
                navItems.map(item => (
                  <button
                    key={item.id}
                    onClick={() => setCurrentView(item.id as any)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      currentView === item.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-accent hover:text-accent-foreground'
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    <span className="hidden sm:inline">{item.label}</span>
                  </button>
                ))
              )}

              <ModeToggle darkMode={darkMode} onToggle={setDarkMode} />
              <ModelSelector
                currentProvider={provider}
                onProviderChange={setAIProvider}
              />
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {currentView === 'chat' && (
          <div className="h-[calc(100vh-140px)]">
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              isConnected={isConnected}
            />
          </div>
        )}

        {currentView === 'envelope' && (
          <div className="h-[calc(100vh-140px)]">
            {envelopeData ? (
              <EnvelopeChart
                data={envelopeData}
                onDataChange={handleEnvelopeChange}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-semibold mb-2">包络图</h3>
                  <p className="text-muted-foreground mb-4">
                    请先在聊天中生成包络图数据
                  </p>
                  <div className="bg-muted rounded-lg p-4 text-sm">
                    <p className="font-medium mb-2">您可以尝试以下命令：</p>
                    <ul className="space-y-2 text-left">
                      <li>• "生成W/S vs T/W包络图"</li>
                      <li>• "生成高度vs速度包络图"</li>
                      <li>• "生成升力系数vs攻角包络图"</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {currentView === '3d' && (
          <div className="h-[calc(100vh-140px)]">
            <Model3DViewer
              modelUrl={modelData?.url}
              showGrid={true}
              showAxes={true}
              showWireframe={false}
              backgroundColor={darkMode ? '#1a1a2e' : '#ffffff'}
            />
          </div>
        )}

        {currentView === 'settings' && <Settings />}

        {currentView === 'history' && <History />}
      </main>

      <footer className="border-t bg-muted/50 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>© 2024 飞机设计系统. 基于 SKILL 和 AI 技术构建.</p>
          <div className="flex items-center justify-center gap-4 mt-2">
            <a href="https://github.com/yourusername/aircraft-design-skill" target="_blank" rel="noopener noreferrer" className="hover:text-foreground">
              GitHub
            </a>
            <a href="https://github.com/yourusername/aircraft-design-skill/issues" target="_blank" rel="noopener noreferrer" className="hover:text-foreground">
              问题反馈
            </a>
            <a href="/docs" className="hover:text-foreground">
              文档
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
