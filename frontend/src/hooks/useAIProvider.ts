
import { useState, useEffect } from 'react'

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
  temperature?: number
  maxTokens?: number
  topP?: number
}

export interface ProviderInfo {
    name: string
    enabled: bool
    model: string
    baseUrl: string
}

export function useAIProvider() {
  const [provider, setProvider] = useState<AIProvider>('openai')
  const [config, setConfig] = useState<AIProviderConfig | null>(null)
  const [availableModels, setAvailableModels] = useState<AIModel[]>([])
  const [providersList, setProvidersList] = useState<ProviderInfo[]>([])

  const API_BASE = '/api/ai'

  const fetchProviders = async () => {
    try {
        const res = await fetch(`${API_BASE}/providers`)
        if (res.ok) {
            const data = await res.json()
            setProvidersList(data)
            // If there are configured providers, select the first one or current one if valid
            if (data.length > 0) {
                 const current = data.find((p: ProviderInfo) => p.name === provider)
                 if (!current) {
                     setProvider(data[0].name as AIProvider)
                 }
            }
        }
    } catch (e) {
        console.error("Failed to fetch providers", e)
    }
  }

  const saveConfig = async (newConfig: AIProviderConfig) => {
      try {
          const res = await fetch(`${API_BASE}/configure`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify(newConfig)
          })
          if (res.ok) {
              setConfig(newConfig)
              setProvider(newConfig.provider)
              await fetchProviders() // Refresh list
              return true
          } else {
              const err = await res.json()
              alert(`Error saving config: ${err.detail}`)
              return false
          }
      } catch (e) {
          console.error("Failed to save config", e)
          return false
      }
  }

  useEffect(() => {
    fetchProviders()
  }, [])

  // Mock models for now, but could be fetched from backend capabilities
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
        id: 'claude-3-opus',
        name: 'Claude 3 Opus',
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
        id: 'qwen3:4b',
        name: 'Qwen 3 (4B)',
        provider: 'ollama',
        maxTokens: 4096,
        supportsVision: false,
        supportsCode: true,
        supportsMath: true,
      }
    ]
    setAvailableModels(models.filter(m => m.provider === provider))
  }, [provider])

  return {
    provider,
    setProvider,
    config,
    setConfig, // Note: This updates local state, use saveConfig to persist
    availableModels,
    saveConfig,
    providersList
  }
}
