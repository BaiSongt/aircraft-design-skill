
import { useState, useEffect, useRef, useCallback } from 'react'

export interface StreamEvent {
  type: 'message_chunk' | 'tool_start' | 'tool_end' | 'error' | 'message'
  content?: string
  tool_name?: string
  tool_input?: any
  tool_output?: any
  message_id?: string
}

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  isStreaming?: boolean
  toolCalls?: ToolCallInfo[]
}

export interface ToolCallInfo {
  id: string
  name: string
  input: any
  output?: any
  status: 'running' | 'completed' | 'failed'
}

export function useWebSocket(url: string = 'ws://localhost:8000/ws/client_1') {
  const [isConnected, setIsConnected] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const socketRef = useRef<WebSocket | null>(null)
  
  // Keep track of the current streaming message ID
  const currentMessageIdRef = useRef<string | null>(null)

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return

    const socket = new WebSocket(url)
    socketRef.current = socket

    socket.onopen = () => {
      setIsConnected(true)
      console.log('WebSocket connected')
    }

    socket.onclose = () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
      // Simple reconnect logic
      setTimeout(connect, 3000)
    }

    socket.onmessage = (event) => {
      try {
        const data: StreamEvent = JSON.parse(event.data)
        handleStreamEvent(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      socketRef.current?.close()
    }
  }, [connect])

  const handleStreamEvent = (event: StreamEvent) => {
    setMessages(prev => {
      const newMessages = [...prev]
      
      // Helper to find or create the current assistant message
      const getOrCreateAssistantMessage = () => {
        let msg = newMessages.find(m => m.id === currentMessageIdRef.current)
        if (!msg) {
          msg = {
            id: currentMessageIdRef.current || Date.now().toString(),
            type: 'assistant',
            content: '',
            timestamp: Date.now(),
            isStreaming: true,
            toolCalls: []
          }
          currentMessageIdRef.current = msg.id
          newMessages.push(msg)
        }
        return msg
      }

      switch (event.type) {
        case 'message_chunk':
          const msg = getOrCreateAssistantMessage()
          msg.content += event.content || ''
          break

        case 'tool_start':
          const toolMsg = getOrCreateAssistantMessage()
          toolMsg.toolCalls = toolMsg.toolCalls || []
          toolMsg.toolCalls.push({
            id: Date.now().toString(), // Simple ID generation
            name: event.tool_name || 'unknown',
            input: event.tool_input,
            status: 'running'
          })
          break

        case 'tool_end':
          const endMsg = getOrCreateAssistantMessage()
          if (endMsg.toolCalls && endMsg.toolCalls.length > 0) {
            const lastTool = endMsg.toolCalls[endMsg.toolCalls.length - 1]
            lastTool.output = event.tool_output
            lastTool.status = 'completed'
          }
          break
        
        case 'error':
           newMessages.push({
             id: Date.now().toString(),
             type: 'system',
             content: `Error: ${event.content}`,
             timestamp: Date.now()
           })
           break
      }
      return newMessages
    })
  }

  const sendMessage = (content: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      // Reset current message ID for new response
      currentMessageIdRef.current = (Date.now() + 1).toString()
      
      // Add user message locally
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'user',
        content,
        timestamp: Date.now()
      }])

      // Send to backend
      socketRef.current.send(JSON.stringify({
        type: 'chat',
        content
      }))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  return {
    isConnected,
    messages,
    sendMessage
  }
}
