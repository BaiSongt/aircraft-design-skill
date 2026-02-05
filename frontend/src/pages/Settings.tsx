
import { useState, useEffect } from 'react'
import { Save, Trash2, Plus, Eye, EyeOff, Settings as SettingsIcon, Moon, Sun } from 'lucide-react'
import { useAIProvider, AIProviderConfig } from '@/hooks/useAIProvider'
import { ModeToggle } from '@/components/ModeToggle'

export function Settings() {
  const { provider, setProvider, config, setConfig, saveConfig, providersList } = useAIProvider()
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved === 'true'
  })

  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({})

  useEffect(() => {
    localStorage.setItem('darkMode', String(darkMode))
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  // Sync local config state when provider changes
  useEffect(() => {
      // Find if we have an existing config for this provider in the list
      const existing = providersList.find(p => p.name === provider)
      if (existing) {
          // We might not get the full config (like API key) back for security, 
          // but we can set what we have. 
          // For now, we'll just reset the form or keep previous values if same provider.
          setConfig({
              provider: provider,
              apiKey: '', // Don't show existing key for security usually
              baseUrl: existing.baseUrl,
              model: existing.model
          })
      } else {
          setConfig({
              provider: provider,
              apiKey: '',
              baseUrl: '',
              model: ''
          })
      }
  }, [provider, providersList, setConfig])


  const handleSaveConfig = async () => {
    if (!config) return
    if (!config.apiKey && provider !== 'ollama') { // Ollama might not need key
      alert('请输入API Key')
      return
    }

    const success = await saveConfig(config)
    if (success) {
        alert('配置已保存')
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
    ollama: 'Ollama',
    localai: 'LocalAI',
    vllm: 'vLLM',
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <SettingsIcon className="w-8 h-8" />
          设置
        </h1>
        <ModeToggle />
      </div>

      <div className="grid gap-6">
        {/* AI Provider Settings */}
        <div className="bg-card rounded-lg border shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">AI 模型配置</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">选择提供商</label>
              <select
                className="w-full p-2 rounded-md border bg-background"
                value={provider}
                onChange={(e) => setProvider(e.target.value as any)}
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
                  <label className="block text-sm font-medium mb-1">API Key</label>
                  <div className="relative">
                    <input
                      type={showApiKey[provider] ? 'text' : 'password'}
                      className="w-full p-2 rounded-md border bg-background pr-10"
                      value={config.apiKey}
                      onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                      placeholder={`输入 ${providerNames[provider]} API Key`}
                    />
                    <button
                      className="absolute right-2 top-2.5 text-muted-foreground hover:text-foreground"
                      onClick={() => toggleApiKeyVisibility(provider)}
                    >
                      {showApiKey[provider] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Base URL (可选)</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded-md border bg-background"
                    value={config.baseUrl || ''}
                    onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
                    placeholder="例如: https://api.openai.com/v1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">模型名称 (可选)</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded-md border bg-background"
                    value={config.model || ''}
                    onChange={(e) => setConfig({ ...config, model: e.target.value })}
                    placeholder="例如: gpt-4-turbo"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                   <div>
                      <label className="block text-sm font-medium mb-1">Temperature</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="2"
                        className="w-full p-2 rounded-md border bg-background"
                        value={config.temperature ?? 0.7}
                        onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                      />
                   </div>
                   <div>
                      <label className="block text-sm font-medium mb-1">Max Tokens</label>
                      <input
                        type="number"
                        step="1"
                        className="w-full p-2 rounded-md border bg-background"
                        value={config.maxTokens ?? 4096}
                        onChange={(e) => setConfig({ ...config, maxTokens: parseInt(e.target.value) })}
                      />
                   </div>
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
                    onClick={handleSaveConfig}
                  >
                    <Save className="w-4 h-4" />
                    保存配置
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Existing Configurations List */}
        <div className="bg-card rounded-lg border shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">已配置的模型</h2>
          <div className="space-y-2">
            {providersList.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无配置</p>
            ) : (
              providersList.map((p) => (
                <div key={p.name} className="flex justify-between items-center p-3 border rounded-md">
                  <div>
                    <span className="font-medium">{providerNames[p.name] || p.name}</span>
                    {p.model && <span className="ml-2 text-xs bg-secondary px-2 py-1 rounded text-secondary-foreground">{p.model}</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${p.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                    <span className="text-sm text-muted-foreground">{p.enabled ? '已启用' : '未启用'}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
