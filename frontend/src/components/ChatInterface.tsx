import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, MessageSquare } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { Prism as SyntaxHighlighterTheme } from 'react-syntax-highlighter/dist/esm/styles/prism-tomorrow'

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
              components={{
                code: ({ node, inline, ...props }: any) => {
                  const match = /language-(\w+)/.exec(node.className || '') || 'language-text'
                  const language = match ? match[1] : 'text'

                  return (
                    <SyntaxHighlighter
                      language={language}
                      style={SyntaxHighlighterTheme}
                      PreTag="div"
                      className="rounded-md"
                      {...props}
                    >
                      {String(node.children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  )
                },
              }}
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
              <p className="text-muted-foreground mb-4">
                请输入您的设计需求，AI将帮助您调用SKILL模块进行飞机设计。
              </p>
              <div className="bg-muted rounded-lg p-4 text-sm">
                <p className="font-medium mb-2">您可以尝试以下命令：</p>
                <ul className="space-y-2 text-left">
                  <li>• "设计一架机翼，面积30m²，展弦比8.0"</li>
                  <li>• "创建机身，长度15m，直径2m"</li>
                  <li>• "生成包络图，W/S vs T/W"</li>
                  <li>• "查看3D模型"</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id}>
              {renderMessage(message)}
            </div>
          ))
        )}
      </div>

      <div className="border-t bg-background p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 mb-4">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入您的设计需求..."
                disabled={!isConnected || isLoading}
                className="w-full min-h-[60px] max-h-[200px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                rows={1}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || !isConnected || isLoading}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-950 disabled:opacity-50 disabled:pointer-events-none bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 h-[60px]"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>

          {isTyping && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>AI正在思考...</span>
            </div>
          )}

          {!isConnected && (
            <div className="flex items-center gap-2 text-sm text-destructive">
              <MessageSquare className="h-4 w-4" />
              <span>连接已断开，正在重连...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
