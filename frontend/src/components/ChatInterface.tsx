import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, MessageSquare } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

import { useSkillCalls } from '@/hooks/useSkillCalls'
import { useWebSocket } from '@/hooks/useWebSocket'

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

export interface ChatInterfaceProps {
  messages: ChatMessage[]
  onSendMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  isConnected: boolean
}

export function ChatInterface({ messages, onSendMessage, isConnected }: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { isLoading, callSkill } = useSkillCalls()
  const { sendMessage: sendWebSocketMessage } = useWebSocket()

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || !isConnected) {
      return
    }

    setIsTyping(true)

    const userMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
      type: 'user',
      content: input.trim(),
    }

    onSendMessage(userMessage)

    try {
      const result = await callSkill({
        skill: 'ai_chat',
        method: 'chat',
        parameters: {
          message: input.trim(),
        },
      })

      if (result.success) {
        sendWebSocketMessage({
          type: 'message',
          content: input.trim(),
        })
      } else {
        onSendMessage({
          type: 'system',
          content: `Error: ${result.error}`,
        })
      }
    } catch (error) {
      console.error('Error sending message:', error)
      onSendMessage({
        type: 'system',
        content: `Error: ${error}`,
      })
    } finally {
      setInput('')
      setIsTyping(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const renderMessage = (message: ChatMessage) => {
    if (message.type === 'user') {
      return (
        <div className="flex justify-end mb-4">
          <div className="max-w-[80%] rounded-lg bg-primary text-primary-foreground p-3">
            <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
          </div>
        </div>
      )
    } else if (message.type === 'assistant') {
      return (
        <div className="flex justify-start mb-4">
          <div className="max-w-[80%] rounded-lg bg-muted text-muted-foreground p-3">
            <ReactMarkdown
              className="prose prose-sm dark:prose-invert max-w-none"
            />
          </div>
        </div>
      )
    } else {
      return (
        <div className="flex justify-center mb-4">
          <div className="max-w-[80%] rounded-lg bg-destructive/10 text-destructive-foreground p-3">
            <p className="text-sm font-medium">{message.content}</p>
          </div>
        </div>
      )
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4" ref={messagesEndRef}>
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">欢迎使用飞机设计系统</h3>
              <p className="text-sm text-muted-foreground mb-4">
                请输入您的问题，我将使用 AI 技术为您提供专业的飞机设计建议。
              </p>
              <div className="text-xs text-muted-foreground">
                <p className="mb-1">• 支持多种 AI 模型（OpenAI、Anthropic、Google 等）</p>
                <p className="mb-1">• 实时对话和技能调用</p>
                <p>• 专业的飞机设计分析</p>
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id}>{renderMessage(message)}</div>
          ))
        )}
      </div>
      <div className="border-t p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入您的问题..."
            className="flex-1 rounded-md border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 min-h-[60px]"
            disabled={!isConnected || isTyping}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !isConnected || isTyping}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
          >
            {isTyping ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
