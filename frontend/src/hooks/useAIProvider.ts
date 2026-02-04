import { useState, useCallback, useEffect } from 'react'

export type AIProvider =
  | 'openai'
  | 'anthropic'
  | 'google'
  | 'tongyi'
  | 'zhipu'
  | 'deepseek'
  | 'moonshot'
  | 'ollama'
  | 'localai'
  | 'vllm'
  | 'custom'

export interface AIModel {
  id: string
  name: string
  provider: AIProvider
  maxTokens: number
  supportsVision: boolean
  supportsCode: boolean
  supportsMath: boolean
}

export interface AIProviderConfig {
  provider: AIProvider
  apiKey: string
  baseUrl?: string
  model?: string
}

export function useAIProvider() {
  const [provider, setProvider] = useState<AIProvider>(() => {
    const saved = localStorage.getItem('aiProvider')
    return (saved as AIProvider) || 'openai'
  })

  const [config, setConfig] = useState<AIProviderConfig | null>(() => {
    const saved = localStorage.getItem('aiProviderConfig')
    return saved ? JSON.parse(saved) : null
  })

  const [availableModels, setAvailableModels] = useState<AIModel[]>([])

  useEffect(() => {
    const models: AIModel[] = [
      {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        maxTokens: 8192,
        supportsVision: true,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'gpt-4-turbo',
        name: 'GPT-4 Turbo',
        provider: 'openai',
        maxTokens: 4096,
        supportsVision: false,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'claude-3-opus',
        name: 'Claude 3 Opus',
        provider: 'anthropic',
        maxTokens: 200000,
        supportsVision: true,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'claude-3-sonnet',
        name: 'Claude 3 Sonnet',
        provider: 'anthropic',
        maxTokens: 200000,
        supportsVision: true,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'gemini-pro',
        name: 'Gemini Pro',
        provider: 'google',
        maxTokens: 32768,
        supportsVision: true,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'tongyi-qianwen',
        name: '通义千问',
        provider: 'tongyi',
        maxTokens: 8192,
        supportsVision: true,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'zhipu-glm-4',
        name: '智谱 GLM-4',
        provider: 'zhipu',
        maxTokens: 8192,
        supportsVision: false,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'deepseek-chat',
        name: 'DeepSeek Chat',
        provider: 'deepseek',
        maxTokens: 32768,
        supportsVision: false,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'moonshot-v1',
        name: '月之暗面 V1',
        provider: 'moonshot',
        maxTokens: 32768,
        supportsVision: true,
        supportsCode: true,
        supportsMath: true,
      },
      {
        id: 'ollama-llama3',
        name: 'Ollama Llama3',
        provider: 'ollama',
        maxTokens: 4096,
        supportsVision: false,
        supportsCode: true,
        supportsMath: false,
      },
      {
        id: 'localai',
        name: 'LocalAI',
        provider: 'localai',
        maxTokens: 4096,
        supportsVision: false,
        supportsCode: true,
        supportsMath: false,
      },
      {
        id: 'vllm',
        name: 'vLLM',
        provider: 'vllm',
        maxTokens: 4096,
        supportsVision: false,
        supportsCode: true,
        supportsMath: false,
      },
    ]
    setAvailableModels(models)
  }, [])

  const setAIProvider = useCallback((newProvider: AIProvider, newConfig: AIProviderConfig) => {
    setProvider(newProvider)
    setConfig(newConfig)
    localStorage.setItem('aiProvider', newProvider)
    localStorage.setItem('aiProviderConfig', JSON.stringify(newConfig))
  }, [])

  const getModelsByProvider = useCallback((provider: AIProvider): AIModel[] => {
    return availableModels.filter(model => model.provider === provider)
  }, [availableModels])

  return {
    provider,
    config,
    availableModels,
    setAIProvider,
    getModelsByProvider,
  }
}
