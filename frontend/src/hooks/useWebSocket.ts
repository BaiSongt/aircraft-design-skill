import { useState, useEffect, useCallback, useRef } from 'react'
import { io, Socket } from 'socket.io-client'

export type MessageType =
  | 'message'
  | 'progress'
  | 'result'
  | 'error'
  | 'calculation_start'
  | 'calculation_complete'

export interface Message {
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

export interface ProgressUpdate {
  taskId: string
  progress: number
  status: string
  currentStep: string
}

export interface CalculationResult {
  taskId: string
  result: any
  duration: number
  success: boolean
}

export function useWebSocket(url: string = 'ws://localhost:8000') {
  const [isConnected, setIsConnected] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [progress, setProgress] = useState<Record<string, ProgressUpdate>>({})
  const [results, setResults] = useState<Record<string, CalculationResult>>({})
  const socketRef = useRef<Socket | null>(null)

  useEffect(() => {
    const socket = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    })

    socketRef.current = socket

    socket.on('connect', () => {
      setIsConnected(true)
      console.log('WebSocket connected')
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    })

    socket.on('message', (data: Message) => {
      setMessages(prev => [...prev, data])
    })

    socket.on('progress', (data: ProgressUpdate) => {
      setProgress(prev => ({
        ...prev,
        [data.taskId]: data,
      }))
    })

    socket.on('result', (data: CalculationResult) => {
      setResults(prev => ({
        ...prev,
        [data.taskId]: data,
      }))
    })

    socket.on('error', (data: { taskId: string, error: string }) => {
      console.error('Calculation error:', data)
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'system',
        content: `计算错误: ${data.error}`,
        timestamp: Date.now(),
        metadata: { error: data.error },
      }])
    })

    return () => {
      socket.disconnect()
      setIsConnected(false)
    }
  }, [url])

  const sendMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    if (!socketRef.current || !isConnected) {
      console.error('WebSocket not connected')
      return
    }

    const fullMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: Date.now(),
    }

    socketRef.current.emit('message', fullMessage)
  }, [isConnected])

  const clearMessages = useCallback(() => {
    setMessages([])
    setProgress({})
    setResults({})
  }, [])

  const clearTaskProgress = useCallback((taskId: string) => {
    setProgress(prev => {
      const newProgress = { ...prev }
      delete newProgress[taskId]
      return newProgress
    })
  }, [])

  return {
    isConnected,
    messages,
    progress,
    results,
    sendMessage,
    clearMessages,
    clearTaskProgress,
  }
}
