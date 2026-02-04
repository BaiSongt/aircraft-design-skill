import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(value: number, decimals: number = 2): string {
  return value.toFixed(decimals)
}

export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(() => func(...args), wait)
  }
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

export function downloadFile(data: string, filename: string, type: string = 'text/plain') {
  const blob = new Blob([data], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function copyToClipboard(text: string): Promise<boolean> {
  return navigator.clipboard.writeText(text).then(
    () => true,
    () => false
  )
}

export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export function validateUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function parseJsonSafely<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json) as T
  } catch {
    return fallback
  }
}

export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj)) as T
}

export function isEmpty(obj: any): boolean {
  if (obj === null || obj === undefined) {
    return true
  }
  if (typeof obj === 'string') {
    return obj.trim().length === 0
  }
  if (Array.isArray(obj)) {
    return obj.length === 0
  }
  if (typeof obj === 'object') {
    return Object.keys(obj).length === 0
  }
  return false
}

export function mergeDeep<T extends object>(target: T, source: Partial<T>): T {
  const output = { ...target }

  for (const key in source) {
    if (source[key] instanceof Object && key in target) {
      output[key] = mergeDeep(target[key], source[key] as any)
    } else {
      output[key] = source[key] as any
    }
  }

  return output
}
