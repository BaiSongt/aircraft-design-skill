import { useState, useEffect } from 'react'
import { Save, Trash2, Plus, Eye, EyeOff, Settings as SettingsIcon, Moon, Sun } from 'lucide-react'
import { useAIProvider } from '@/hooks/useAIProvider'
import { ModeToggle } from '@/components/ModeToggle'

export interface AIProviderConfig {
  provider: string
  apiKey: string
  baseUrl?: string
  model?: string
  temperature?: number
  maxTokens?: number
  topP?: number
}

export function Settings() {
  const { provider, config, setAIProvider } = useAIProvider()
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved === 'true'
  })

  const [savedConfigs, setSavedConfigs] = useState<AIProviderConfig[]>(() => {
    const saved = localStorage.getItem('aiProviderConfigs')
    return saved ? JSON.parse(saved) : []
  })

  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({})

  useEffect(() => {
    localStorage.setItem('aiProviderConfigs', JSON.stringify(savedConfigs))
  }, [savedConfigs])

  useEffect(() => {
    localStorage.setItem('darkMode', String(darkMode))
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  const handleSaveConfig = () => {
    if (!config?.apiKey) {
      alert('请输入API Key')
      return
    }

    const newConfig: AIProviderConfig = {
      provider,
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
      model: config.model,
      temperature: config.temperature,
      maxTokens: config.maxTokens,
      topP: config.topP,
    }

    const existingIndex = savedConfigs.findIndex(c => c.provider === provider)
    if (existingIndex >= 0) {
      const newConfigs = [...savedConfigs]
      newConfigs[existingIndex] = newConfig
      setSavedConfigs(newConfigs)
    } else {
      setSavedConfigs([...savedConfigs, newConfig])
    }

    alert('配置已保存')
  }

  const handleDeleteConfig = (provider: string) => {
    const newConfigs = savedConfigs.filter(c => c.provider !== provider)
    setSavedConfigs(newConfigs)

    if (provider === savedConfigs[savedConfigs.length - 1]?.provider) {
      setAIProvider(savedConfigs[0].provider, savedConfigs[0])
    }
  }

  const handleLoadConfig = (config: AIProviderConfig) => {
    setAIProvider(config.provider, config)
  }

  const handleClearAllConfigs = () => {
    if (confirm('确定要清除所有配置吗？')) {
      setSavedConfigs([])
      localStorage.removeItem('aiProviderConfigs')
    }
  }

  const toggleApiKeyVisibility = (provider: string) => {
    setShowApiKey(prev => ({
      ...prev,
      [provider]: !prev[provider],
    }))
  }

  const providerNames: Record<string, string> = {
    openai: 'OpenAI GPT-4',
    anthropic: 'Anthropic Claude 3',
    google: 'Google Gemini Pro',
    tongyi: '通义千问',
    zhipu: '智谱AI GLM-4',
    deepseek: 'DeepSeek Chat',
    moonshot: '月之暗面 V1',
    ollama: 'Ollama Llama3',
    localai: 'LocalAI',
    vllm: 'vLLM',
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">设置</h1>
          <p className="text-muted-foreground">配置AI提供商和应用设置</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-6">
            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <SettingsIcon className="h-5 w-5" />
                AI提供商配置
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">当前AI提供商</label>
                  <select
                    value={provider}
                    onChange={(e) => {
                      const selectedConfig = savedConfigs.find(c => c.provider === e.target.value)
                      if (selectedConfig) {
                        handleLoadConfig(selectedConfig)
                      }
                    }}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                  >
                    {Object.entries(providerNames).map(([key, name]) => (
                      <option key={key} value={key}>
                        {name}
                      </option>
                    ))}
                  </select>
                </div>

                {config && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-2">API Key</label>
                      <div className="relative">
                        <input
                          type={showApiKey[provider] ? 'text' : 'password'}
                          value={config.apiKey}
                          onChange={(e) => setAIProvider(provider, { ...config, apiKey: e.target.value })}
                          placeholder="输入API Key..."
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                        />
                        <button
                          onClick={() => toggleApiKeyVisibility(provider)}
                          className="absolute right-3 top-1/2 -translate-y-1/2"
                        >
                          {showApiKey[provider] ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </button>
                      </div>
                    </div>

                    {config.baseUrl && (
                      <div>
                        <label className="block text-sm font-medium mb-2">Base URL</label>
                        <input
                          type="text"
                          value={config.baseUrl}
                          onChange={(e) => setAIProvider(provider, { ...config, baseUrl: e.target.value })}
                          placeholder="自定义Base URL..."
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                        />
                      </div>
                    )}

                    {config.model && (
                      <div>
                        <label className="block text-sm font-medium mb-2">模型名称</label>
                        <input
                          type="text"
                          value={config.model}
                          onChange={(e) => setAIProvider(provider, { ...config, model: e.target.value })}
                          placeholder="自定义模型名称..."
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                        />
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium mb-2">Temperature</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="2"
                        value={config.temperature || 0.7}
                        onChange={(e) => setAIProvider(provider, { ...config, temperature: parseFloat(e.target.value) })}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Max Tokens</label>
                      <input
                        type="number"
                        min="1"
                        max="128000"
                        value={config.maxTokens || 4096}
                        onChange={(e) => setAIProvider(provider, { ...config, maxTokens: parseInt(e.target.value) })}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Top P</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        value={config.topP || 1.0}
                        onChange={(e) => setAIProvider(provider, { ...config, topP: parseFloat(e.target.value) })}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                      />
                    </div>

                    <button
                      onClick={handleSaveConfig}
                      className="w-full rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-950 bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2"
                    >
                      <Save className="h-4 w-4 mr-2" />
                      保存配置
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <SettingsIcon className="h-5 w-5" />
                已保存的配置
              </h2>

              <div className="space-y-2">
                {savedConfigs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <p className="mb-2">还没有保存的配置</p>
                    <p className="text-sm">保存配置后可以快速切换</p>
                  </div>
                ) : (
                  savedConfigs.map((savedConfig, index) => (
                    <div
                      key={savedConfig.provider}
                      className="flex items-center justify-between p-3 rounded-md border border-input bg-background hover:bg-accent transition-colors"
                    >
                      <div className="flex-1">
                        <div className="font-medium">{providerNames[savedConfig.provider]}</div>
                        <div className="text-sm text-muted-foreground">
                          {savedConfig.model || '默认模型'}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleLoadConfig(savedConfig)}
                          className="px-3 py-1.5 rounded-md text-sm font-medium transition-colors hover:bg-accent"
                          title="加载配置"
                        >
                          <Plus className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteConfig(savedConfig.provider)}
                          className="px-3 py-1.5 rounded-md text-sm font-medium transition-colors hover:bg-destructive/10 text-destructive"
                          title="删除配置"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                )}

                {savedConfigs.length > 0 && (
                  <button
                    onClick={handleClearAllConfigs}
                    className="w-full mt-4 rounded-md text-sm font-medium transition-colors hover:bg-destructive/10 text-destructive px-4 py-2"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    清除所有配置
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <SettingsIcon className="h-5 w-5" />
                应用设置
              </h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {darkMode ? (
                      <Moon className="h-5 w-5" />
                    ) : (
                      <Sun className="h-5 w-5" />
                    )}
                    <span className="font-medium">主题模式</span>
                  </div>
                  <ModeToggle darkMode={darkMode} onToggle={setDarkMode} />
                </div>

                <div className="flex items-center justify-between">
                  <span className="font-medium">语言</span>
                  <select
                    defaultValue="zh-CN"
                    className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                  >
                    <option value="zh-CN">简体中文</option>
                    <option value="en-US">English</option>
                  </select>
                </div>

                <div className="flex items-center justify-between">
                  <span className="font-medium">默认页面大小</span>
                  <select
                    defaultValue="10"
                    className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                  >
                    <option value="10">10条/页</option>
                    <option value="20">20条/页</option>
                    <option value="50">50条/页</option>
                    <option value="100">100条/页</option>
                  </select>
                </div>

                <div className="flex items-center justify-between">
                  <span className="font-medium">自动保存</span>
                  <select
                    defaultValue="true"
                    className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                  >
                    <option value="true">启用</option>
                    <option value="false">禁用</option>
                  </select>
                </div>

                <div className="flex items-center justify-between">
                  <span className="font-medium">通知</span>
                  <select
                    defaultValue="all"
                    className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                  >
                    <option value="all">全部通知</option>
                    <option value="important">仅重要通知</option>
                    <option value="none">不显示通知</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <SettingsIcon className="h-5 w-5" />
                关于
              </h2>

              <div className="space-y-3">
                <div>
                  <div className="font-medium">版本</div>
                  <div className="text-sm text-muted-foreground">1.0.0</div>
                </div>
                <div>
                  <div className="font-medium">更新时间</div>
                  <div className="text-sm text-muted-foreground">2024-01-15</div>
                </div>
                <div>
                  <div className="font-medium">许可证</div>
                  <div className="text-sm text-muted-foreground">MIT License</div>
                </div>
                <div>
                  <div className="font-medium">技术支持</div>
                  <div className="text-sm text-muted-foreground">
                    <a href="https://github.com/yourusername/aircraft-design-skill" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                      GitHub Issues
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
