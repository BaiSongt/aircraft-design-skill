import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ModeToggle } from '@/components/ModeToggle'

describe('ModeToggle', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('应该正确渲染', () => {
    render(<ModeToggle darkMode={false} onToggle={() => {}} />)
    expect(screen.getByRole('button', { name: 'Toggle theme' })).toBeInTheDocument()
  })

  it('应该在点击时切换暗色模式', () => {
    const onToggle = vi.fn()
    render(<ModeToggle darkMode={false} onToggle={onToggle} />)

    const button = screen.getByRole('button', { name: 'Toggle theme' })
    fireEvent.click(button)

    expect(onToggle).toHaveBeenCalledWith(true)
  })

  it('应该保存暗色模式到localStorage', () => {
    render(<ModeToggle darkMode={true} onToggle={() => {}} />)
    
    expect(localStorage.getItem('darkMode')).toBe('true')
  })
})
