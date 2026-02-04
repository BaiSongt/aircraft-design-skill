import { useState, useEffect } from 'react'
import { ModeToggle } from '@/components/ModeToggle'
import { ChatInterface } from '@/components/ChatInterface'
import { ModelSelector } from '@/components/ModelSelector'
import { EnvelopeChart } from '@/components/EnvelopeChart'
import { Model3DViewer } from '@/components/Model3DViewer'
import { ResultTable } from '@/components/ResultTable'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useAIProvider } from '@/hooks/useAIProvider'

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved === 'true'
  })

  const [currentView, setCurrentView] = useState<'chat' | 'envelope' | '3d'>('chat')

  const { aiProvider, setAIProvider } = useAIProvider()
  const { isConnected, messages, sendMessage } = useWebSocket()

  useEffect(() => {
    localStorage.setItem('darkMode', String(darkMode))
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <div className={`min-h-screen bg-background text-foreground ${darkMode ? 'dark' : ''}`}>
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">
              飞机设计系统
            </h1>
            <div className="flex items-center gap-4">
              <ModeToggle darkMode={darkMode} onToggle={setDarkMode} />
              <ModelSelector
                currentProvider={aiProvider}
                onProviderChange={setAIProvider}
              />
            </div>
          </div>
        </div>
      </header>

      <nav className="border-b bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentView('chat')}
              className={`px-4 py-2 rounded-md transition-colors ${
                currentView === 'chat'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              聊天
            </button>
            <button
              onClick={() => setCurrentView('envelope')}
              className={`px-4 py-2 rounded-md transition-colors ${
                currentView === 'envelope'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              包络图
            </button>
            <button
              onClick={() => setCurrentView('3d')}
              className={`px-4 py-2 rounded-md transition-colors ${
                currentView === '3d'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              3D模型
            </button>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-6">
        {currentView === 'chat' && (
          <ChatInterface
            messages={messages}
            onSendMessage={sendMessage}
            isConnected={isConnected}
          />
        )}
        {currentView === 'envelope' && <EnvelopeChart />}
        {currentView === '3d' && <Model3DViewer />}
      </main>

      <footer className="border-t bg-muted/50 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>© 2024 飞机设计系统. 基于 SKILL 和 AI 技术构建.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
