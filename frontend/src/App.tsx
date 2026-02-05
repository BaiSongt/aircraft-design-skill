
import { useState, useEffect } from 'react'
import { ModeToggle } from '@/components/ModeToggle'
import { ChatInterface } from '@/components/ChatInterface'
import { ModelSelector } from '@/components/ModelSelector'
import { EnvelopeChart } from '@/components/EnvelopeChart'
import { Model3DViewer } from '@/components/Model3DViewer'
import { ResultTable } from '@/components/ResultTable'
import { Settings } from '@/pages/Settings'
import { History } from '@/pages/History'
import { SkillsPage } from '@/pages/SkillsPage'
import { useAIProvider } from '@/hooks/useAIProvider'
import { useWebSocket } from '@/hooks/useWebSocket'
import { MessageSquare, Home, Settings as SettingsIcon, History as HistoryIcon, BarChart3, Box, Wrench } from 'lucide-react'

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved === 'true'
  })

  const [currentView, setCurrentView] = useState<'chat' | 'envelope' | '3d' | 'settings' | 'history' | 'skills'>('chat')
  const [isMobile, setIsMobile] = useState(false)

  const { provider } = useAIProvider()

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

  return (
    <div className={`min-h-screen bg-background text-foreground flex ${isMobile ? 'flex-col' : ''}`}>
      {/* Sidebar / Navigation */}
      <nav className={`${isMobile ? 'w-full h-16 flex-row px-4' : 'w-16 h-screen flex-col py-4'} border-r bg-muted/30 flex items-center justify-between z-50`}>
        <div className={`flex ${isMobile ? 'flex-row gap-6' : 'flex-col gap-6'} items-center`}>
          <div className="p-2 rounded-lg bg-primary text-primary-foreground">
            <Home className="w-6 h-6" />
          </div>
          
          <button
            onClick={() => setCurrentView('chat')}
            className={`p-2 rounded-lg transition-colors ${currentView === 'chat' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="Chat"
          >
            <MessageSquare className="w-6 h-6" />
          </button>

          <button
            onClick={() => setCurrentView('skills')}
            className={`p-2 rounded-lg transition-colors ${currentView === 'skills' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="Skills & Tools"
          >
            <Wrench className="w-6 h-6" />
          </button>

          <button
            onClick={() => setCurrentView('envelope')}
            className={`p-2 rounded-lg transition-colors ${currentView === 'envelope' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="Flight Envelope"
          >
            <BarChart3 className="w-6 h-6" />
          </button>

          <button
            onClick={() => setCurrentView('3d')}
            className={`p-2 rounded-lg transition-colors ${currentView === '3d' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="3D Model"
          >
            <Box className="w-6 h-6" />
          </button>
        </div>

        <div className={`flex ${isMobile ? 'flex-row gap-4' : 'flex-col gap-6'} items-center`}>
          <button
            onClick={() => setCurrentView('history')}
            className={`p-2 rounded-lg transition-colors ${currentView === 'history' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="History"
          >
            <HistoryIcon className="w-6 h-6" />
          </button>

          <button
            onClick={() => setCurrentView('settings')}
            className={`p-2 rounded-lg transition-colors ${currentView === 'settings' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="Settings"
          >
            <SettingsIcon className="w-6 h-6" />
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden h-screen relative">
        {currentView === 'chat' && <ChatInterface />}
        {currentView === 'skills' && <SkillsPage />}
        {currentView === 'envelope' && <EnvelopeChart data={null} />}
        {currentView === '3d' && <Model3DViewer modelData={null} />}
        {currentView === 'settings' && <Settings />}
        {currentView === 'history' && <History />}
      </main>
    </div>
  )
}

export default App
