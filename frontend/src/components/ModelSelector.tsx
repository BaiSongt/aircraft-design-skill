import { useState, useEffect } from 'react'
import { Settings, ChevronDown, Check, Key, Globe, Lock, Unlock } from 'lucide-react'

export interface AIProvider {
  id: string
  name: string
  provider: string
  enabled: boolean
  model: string
  baseUrl?: string
}

export interface ModelSelectorProps {
  currentProvider: string
  onProviderChange: (provider: string, config: any) => void
}

export function ModelSelector({ currentProvider, onProviderChange }: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState('')

  const providers: AIProvider[] = [
    {
      id: 'openai',
      name: 'OpenAI GPT-4',
      provider: 'openai',
      enabled: true,
      model: 'gpt-4',
      baseUrl: 'https://api.openai.com/v1',
    },
    {
      id: 'anthropic',
      name: 'Anthropic Claude 3',
      provider: 'anthropic',
      enabled: false,
      model: 'claude-3-sonnet-20240229',
      baseUrl: 'https://api.anthropic.com',
    },
    {
      id: 'google',
      name: 'Google Gemini Pro',
      provider: 'google',
      enabled: false,
      model: 'gemini-pro',
      baseUrl: 'https://generativelanguage.googleapis.com',
    },
    {
      id: 'tongyi',
      name: '通义千问',
      provider: 'tongyi',
      enabled: false,
      model: 'tongyi-qianwen',
      baseUrl: 'https://dashscope.aliyuncs.com/api/v1',
    },
    {
      id: 'zhipu',
      name: '智谱AI GLM-4',
      provider: 'zhipu',
      enabled: false,
      model: 'glm-4',
      baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    },
    {
      id: 'deepseek',
      name: 'DeepSeek Chat',
      provider: 'deepseek',
      enabled: false,
      model: 'deepseek-chat',
      baseUrl: 'https://api.deepseek.com',
    },
    {
      id: 'moonshot',
      name: '月之暗面 V1',
      provider: 'moonshot',
      enabled: false,
      model: 'moonshot-v1-8k',
      baseUrl: 'https://api.moonshot.cn/v1',
    },
    {
      id: 'ollama',
      name: 'Ollama Llama3',
      provider: 'ollama',
      enabled: false,
      model: 'llama3',
      baseUrl: 'http://localhost:11434/v1',
    },
    {
      id: 'localai',
      name: 'LocalAI',
      provider: 'localai',
      enabled: false,
      model: 'localai-model',
      baseUrl: 'http://localhost:8080/v1',
    },
    {
      id: 'vllm',
      name: 'vLLM',
      provider: 'vllm',
      enabled: false,
      model: 'vllm-model',
      baseUrl: 'http://localhost:5000/v1',
    },
  ]

  const currentProviderData = providers.find(p => p.id === currentProvider)

  const handleSave = () => {
    if (apiKey.trim()) {
      localStorage.setItem('aiProvider', currentProvider)
      localStorage.setItem('aiProviderConfig', JSON.stringify({
        provider: currentProvider,
        apiKey: apiKey.trim(),
        baseUrl: baseUrl.trim(),
        model: model.trim(),
      }))

      onProviderChange(currentProvider, {
        provider: currentProvider,
        apiKey: apiKey.trim(),
        baseUrl: baseUrl.trim(),
        model: model.trim(),
      })

      setIsOpen(false)
    }
  }

  const handleCancel = () => {
    setApiKey('')
    setBaseUrl('')
    setModel('')
    setIsOpen(false)
  }

  const handleProviderSelect = (provider: string) => {
    const providerData = providers.find(p => p.id === provider)
    if (providerData) {
      setBaseUrl(providerData.baseUrl || '')
      setModel(providerData.model || '')
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors"
      >
        <Globe className="h-4 w-4" />
        <span className="text-sm font-medium">
          {currentProviderData?.name || '选择AI模型'}
        </span>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-12 w-80 bg-popover text-popover-foreground border border-border rounded-lg shadow-lg p-4 z-50">
          <h3 className="text-lg font-semibold mb-4">AI模型配置</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">选择AI提供商</label>
              <select
                value={currentProvider}
                onChange={(e) => handleProviderSelect(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
              >
                {providers.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            {currentProviderData && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-2">API Key</label>
                  <div className="relative">
                    <Key className="absolute left-3 top-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="输入API Key..."
                      className="w-full rounded-md border border-input bg-background pl-10 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                    />
                  </div>
                </div>

                {currentProviderData.baseUrl && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Base URL</label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-1/2 h-4 w-4 text-muted-foreground" />
                      <input
                        type="text"
                        value={baseUrl}
                        onChange={(e) => setBaseUrl(e.target.value)}
                        placeholder="自定义Base URL..."
                        className="w-full rounded-md border border-input bg-background pl-10 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium mb-2">模型名称</label>
                  <div className="relative">
                    <Settings className="absolute left-3 top-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      placeholder="自定义模型名称..."
                      className="w-full rounded-md border border-input bg-background pl-10 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                      />
                    </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Lock className="h-4 w-4" />
                  <span>API Key将安全存储在本地</span>
                </div>
              </>
            )}

            <div className="flex gap-2 pt-4 border-t border-border">
              <button
                onClick={handleSave}
                disabled={!apiKey.trim()}
                className="flex-1 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-950 disabled:opacity-50 disabled:pointer-events-none bg-primary text-primary-foreground hover:bg-primary/90"
              >
                <Check className="h-4 w-4 mr-2" />
                保存配置
              </button>
              <button
                onClick={handleCancel}
                className="flex-1 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-950 bg-secondary text-secondary-foreground hover:bg-secondary/80"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
