import { BaseChatModel } from 'langchain/chat_models/base'
import { ChatOpenAI } from 'langchain/chat_models/openai'
import { ChatAnthropic } from 'langchain/chat_models/anthropic'
import { ChatGoogleGenerativeAI } from 'langchain/chat_models/google_genai'

export interface AIProviderConfig {
  provider: string
  apiKey: string
  baseUrl?: string
  model?: string
  temperature?: number
  maxTokens?: number
  topP?: number
}

export class AIProviderManager {
  private configs: Map<string, AIProviderConfig>

  constructor() {
    this.configs = new Map()
  }

  addProvider(config: AIProviderConfig): void {
    this.configs.set(config.provider, config)
  }

  getProvider(provider: string): AIProviderConfig | undefined {
    return this.configs.get(provider)
  }

  getAllProviders(): AIProviderConfig[] {
    return Array.from(this.configs.values())
  }

  createChatModel(config: AIProviderConfig): BaseChatModel {
    switch (config.provider) {
      case 'openai':
        return new ChatOpenAI({
          openAIApiKey: config.apiKey,
          modelName: config.model || 'gpt-4',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 4096,
          topP: config.topP || 1.0,
        })

      case 'anthropic':
        return new ChatAnthropic({
          anthropicApiKey: config.apiKey,
          modelName: config.model || 'claude-3-sonnet-20240229',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 4096,
          topP: config.topP || 1.0,
        })

      case 'google':
        return new ChatGoogleGenerativeAI({
          apiKey: config.apiKey,
          modelName: config.model || 'gemini-pro',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 32768,
          topP: config.topP || 1.0,
        })

      case 'tongyi':
        return new ChatOpenAI({
          openAIApiKey: config.apiKey,
          modelName: config.model || 'tongyi-qianwen',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 8192,
          topP: config.topP || 1.0,
          configuration: {
            baseURL: config.baseUrl || 'https://dashscope.aliyuncs.com/api/v1',
          },
        })

      case 'zhipu':
        return new ChatOpenAI({
          openAIApiKey: config.apiKey,
          modelName: config.model || 'glm-4',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 8192,
          topP: config.topP || 1.0,
          configuration: {
            baseURL: config.baseUrl || 'https://open.bigmodel.cn/api/paas/v4',
          },
        })

      case 'deepseek':
        return new ChatOpenAI({
          openAIApiKey: config.apiKey,
          modelName: config.model || 'deepseek-chat',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 32768,
          topP: config.topP || 1.0,
          configuration: {
            baseURL: config.baseUrl || 'https://api.deepseek.com',
          },
        })

      case 'moonshot':
        return new ChatOpenAI({
          openAIApiKey: config.apiKey,
          modelName: config.model || 'moonshot-v1-8k',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 8192,
          topP: config.topP || 1.0,
          configuration: {
            baseURL: config.baseUrl || 'https://api.moonshot.cn/v1',
          },
        })

      case 'ollama':
        return new ChatOpenAI({
          openAIApiKey: 'ollama',
          modelName: config.model || 'llama3',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 4096,
          topP: config.topP || 1.0,
          configuration: {
            baseURL: config.baseUrl || 'http://localhost:11434/v1',
          },
        })

      case 'localai':
        return new ChatOpenAI({
          openAIApiKey: 'localai',
          modelName: config.model || 'localai-model',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 4096,
          topP: config.topP || 1.0,
          configuration: {
            baseURL: config.baseUrl || 'http://localhost:8080/v1',
          },
        })

      case 'vllm':
        return new ChatOpenAI({
          openAIApiKey: 'vllm',
          modelName: config.model || 'vllm-model',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 4096,
          topP: config.topP || 1.0,
          configuration: {
            baseURL: config.baseUrl || 'http://localhost:5000/v1',
          },
        })

      default:
        throw new Error(`Unsupported AI provider: ${config.provider}`)
    }
  }

  async chat(
    config: AIProviderConfig,
    messages: any[],
    onProgress?: (progress: number) => void,
  ): Promise<string> {
    const chatModel = this.createChatModel(config)

    let fullResponse = ''
    let progress = 0

    try {
      const stream = await chatModel.stream(messages, {})

      for await (const chunk of stream) {
        if (onProgress) {
          progress += 10
          if (progress > 100) progress = 100
          onProgress(progress)
        }

        if (typeof chunk.content === 'string') {
          fullResponse += chunk.content
        }
      }

      return fullResponse
    } catch (error: any) {
      console.error('AI chat error:', error)
      throw error
    }
  }

  async generateCode(
    config: AIProviderConfig,
    prompt: string,
    language: string = 'python',
  ): Promise<string> {
    const chatModel = this.createChatModel(config)

    const codePrompt = `Please generate ${language} code for the following task:\n\n${prompt}\n\nOnly output the code, no explanations.`

    try {
      const response = await chatModel.invoke([
        { role: 'user', content: codePrompt },
      ])

      return response.content as string
    } catch (error: any) {
      console.error('AI code generation error:', error)
      throw error
    }
  }

  async generateVisualization(
    config: AIProviderConfig,
    data: any,
    visualizationType: string = 'plotly',
  ): Promise<any> {
    const chatModel = this.createChatModel(config)

    const vizPrompt = `Please generate ${visualizationType} visualization code for the following aircraft design data:\n\n${JSON.stringify(data, null, 2)}\n\nGenerate complete, runnable code.`

    try {
      const response = await chatModel.invoke([
        { role: 'user', content: vizPrompt },
      ])

      return response.content as string
    } catch (error: any) {
      console.error('AI visualization error:', error)
      throw error
    }
  }

  validateConfig(config: AIProviderConfig): boolean {
    if (!config.apiKey) {
      return false
    }

    if (config.provider === 'openai' && !config.apiKey.startsWith('sk-')) {
      return false
    }

    if (config.provider === 'anthropic' && !config.apiKey.startsWith('sk-ant-')) {
      return false
    }

    return true
  }

  getProviderCapabilities(provider: string): {
    supportsVision: boolean
    supportsCode: boolean
    supportsMath: boolean
    supportsStreaming: boolean
  } {
    const capabilities: Record<string, any> = {
      openai: { supportsVision: true, supportsCode: true, supportsMath: true, supportsStreaming: true },
      anthropic: { supportsVision: true, supportsCode: true, supportsMath: true, supportsStreaming: true },
      google: { supportsVision: true, supportsCode: true, supportsMath: true, supportsStreaming: true },
      tongyi: { supportsVision: true, supportsCode: true, supportsMath: true, supportsStreaming: true },
      zhipu: { supportsVision: false, supportsCode: true, supportsMath: true, supportsStreaming: true },
      deepseek: { supportsVision: false, supportsCode: true, supportsMath: true, supportsStreaming: true },
      moonshot: { supportsVision: true, supportsCode: true, supportsMath: true, supportsStreaming: true },
      ollama: { supportsVision: false, supportsCode: true, supportsMath: false, supportsStreaming: true },
      localai: { supportsVision: false, supportsCode: true, supportsMath: false, supportsStreaming: true },
      vllm: { supportsVision: false, supportsCode: true, supportsMath: false, supportsStreaming: true },
    }

    return capabilities[provider] || { supportsVision: false, supportsCode: false, supportsMath: false, supportsStreaming: false }
  }
}
