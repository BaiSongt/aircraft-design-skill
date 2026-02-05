
import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, MessageSquare, Code, Wrench, CheckCircle, XCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

import { useWebSocket, ChatMessage, ToolCallInfo } from '@/hooks/useWebSocket'

export interface ChatInterfaceProps {
  // messages are now managed internally by useWebSocket, but we accept initial ones if needed
  initialMessages?: ChatMessage[]
}

export function ChatInterface({ initialMessages = [] }: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { isConnected, messages, sendMessage } = useWebSocket()

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || !isConnected) {
      return
    }
    sendMessage(input.trim())
    setInput('')
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const renderToolCall = (tool: ToolCallInfo) => {
      return (
          <div key={tool.id} className="mt-2 mb-2 p-2 bg-secondary/50 rounded text-xs font-mono border border-border">
              <div className="flex items-center gap-2 mb-1">
                  <Wrench className="w-3 h-3" />
                  <span className="font-semibold">{tool.name}</span>
                  {tool.status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
                  {tool.status === 'completed' && <CheckCircle className="w-3 h-3 text-green-500" />}
                  {tool.status === 'failed' && <XCircle className="w-3 h-3 text-red-500" />}
              </div>
              <div className="pl-5 text-muted-foreground truncate">
                  Input: {JSON.stringify(tool.input)}
              </div>
              {tool.output && (
                  <div className="pl-5 text-muted-foreground mt-1 truncate">
                      Output: {JSON.stringify(tool.output)}
                  </div>
              )}
          </div>
      )
  }

  const renderMessage = (message: ChatMessage) => {
    if (message.type === 'user') {
      return (
        <div key={message.id} className="flex justify-end mb-4">
          <div className="max-w-[80%] rounded-lg bg-primary text-primary-foreground p-3">
            <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
          </div>
        </div>
      )
    }

    return (
      <div key={message.id} className="flex justify-start mb-4">
        <div className="max-w-[80%] rounded-lg bg-muted p-3">
          <div className="flex items-center gap-2 mb-1 text-xs text-muted-foreground">
            <MessageSquare className="w-3 h-3" />
            <span>AI Assistant</span>
          </div>
          
          {/* Tool Calls */}
          {message.toolCalls && message.toolCalls.map(renderToolCall)}

          {/* Message Content */}
          <div className="text-sm prose dark:prose-invert max-w-none break-words">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
          
          {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse"/>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-200px)]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[400px]">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-50">
            <MessageSquare className="w-12 h-12 mb-2" />
            <p>Start a conversation...</p>
          </div>
        ) : (
          messages.map(renderMessage)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-background">
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={isConnected ? "输入您的问题..." : "连接中..."}
            disabled={!isConnected}
            className="w-full min-h-[80px] p-3 pr-12 rounded-md border resize-none focus:outline-none focus:ring-2 focus:ring-primary bg-background"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !isConnected}
            className="absolute right-3 bottom-3 p-2 rounded-md bg-primary text-primary-foreground disabled:opacity-50 hover:bg-primary/90 transition-colors"
          >
            {isConnected ? <Send className="w-4 h-4" /> : <Loader2 className="w-4 h-4 animate-spin" />}
          </button>
        </div>
        <div className="mt-2 text-xs text-center text-muted-foreground">
             Status: {isConnected ? <span className="text-green-500">Connected</span> : <span className="text-red-500">Disconnected</span>}
        </div>
      </div>
    </div>
  )
}
