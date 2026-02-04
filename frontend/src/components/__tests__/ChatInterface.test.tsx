import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatInterface } from '@/components/ChatInterface'
import { useWebSocket } from '@/hooks/useWebSocket'

vi.mock('@/hooks/useWebSocket')

describe('ChatInterface', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('应该正确渲染', () => {
    const { result } = useWebSocket()
    result.current = {
      isConnected: true,
      messages: [],
      sendMessage: vi.fn(),
    }

    render(<ChatInterface messages={[]} onSendMessage={() => {}} isConnected={true} />)

    expect(screen.getByText('欢迎使用飞机设计系统')).toBeInTheDocument()
  })

  it('应该显示欢迎消息', () => {
    const { result } = useWebSocket()
    result.current = {
      isConnected: true,
      messages: [],
      sendMessage: vi.fn(),
    }

    render(<ChatInterface messages={[]} onSendMessage={() => {}} isConnected={true} />)

    expect(screen.getByText('请输入您的设计需求，AI将帮助您调用SKILL模块进行飞机设计。')).toBeInTheDocument()
  })

  it('应该显示示例命令', () => {
    const { result } = useWebSocket()
    result.current = {
      isConnected: true,
      messages: [],
      sendMessage: vi.fn(),
    }

    render(<ChatInterface messages={[]} onSendMessage={() => {}} isConnected={true} />)

    expect(screen.getByText('• "设计一架机翼，面积30m²，展弦比8.0"')).toBeInTheDocument()
    expect(screen.getByText('• "创建机身，长度15m，直径2m"')).toBeInTheDocument()
  })

  it('应该在未连接时显示错误', async () => {
    const { result } = useWebSocket()
    result.current = {
      isConnected: false,
      messages: [],
      sendMessage: vi.fn(),
    }

    render(<ChatInterface messages={[]} onSendMessage={() => {}} isConnected={false} />)

    await waitFor(() => {
      expect(screen.getByText('连接已断开，正在重连...')).toBeInTheDocument()
    })
  })
})
