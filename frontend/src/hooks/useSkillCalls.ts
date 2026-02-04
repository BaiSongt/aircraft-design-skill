import { useState, useCallback } from 'react'
import axios from 'axios'

export interface SkillCallParams {
  skill: string
  method: string
  parameters: Record<string, any>
}

export interface SkillCallResult {
  success: boolean
  result?: any
  error?: string
  taskId?: string
}

export function useSkillCalls() {
  const [isLoading, setIsLoading] = useState(false)
  const [currentTask, setCurrentTask] = useState<string | null>(null)

  const callSkill = useCallback(async (params: SkillCallParams): Promise<SkillCallResult> => {
    setIsLoading(true)
    setCurrentTask(params.skill)

    try {
      const response = await axios.post('/api/skill/call', params)

      if (response.data.taskId) {
        return {
          success: true,
          taskId: response.data.taskId,
        }
      }

      return {
        success: true,
        result: response.data.result,
      }
    } catch (error: any) {
      console.error('Skill call error:', error)
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Unknown error',
      }
    } finally {
      setIsLoading(false)
      setCurrentTask(null)
    }
  }, [])

  const callSkillWithProgress = useCallback(async (params: SkillCallParams, onProgress?: (progress: number) => void): Promise<SkillCallResult> => {
    setIsLoading(true)
    setCurrentTask(params.skill)

    try {
      const response = await axios.post('/api/skill/call', {
        ...params,
        withProgress: true,
      })

      const taskId = response.data.taskId

      if (taskId && onProgress) {
        const interval = setInterval(async () => {
          try {
            const progressResponse = await axios.get(`/api/skill/progress/${taskId}`)
            onProgress(progressResponse.data.progress)
          } catch (error) {
            console.error('Progress check error:', error)
          }
        }, 500)

        const finalResponse = await axios.get(`/api/skill/result/${taskId}`)
        clearInterval(interval)

        return {
          success: true,
          result: finalResponse.data.result,
          taskId,
        }
      }

      return {
        success: true,
        result: response.data.result,
        taskId,
      }
    } catch (error: any) {
      console.error('Skill call error:', error)
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Unknown error',
      }
    } finally {
      setIsLoading(false)
      setCurrentTask(null)
    }
  }, [])

  const cancelTask = useCallback(async (taskId: string): Promise<boolean> => {
    try {
      await axios.post(`/api/skill/cancel/${taskId}`)
      return true
    } catch (error: any) {
      console.error('Cancel task error:', error)
      return false
    }
  }, [])

  return {
    isLoading,
    currentTask,
    callSkill,
    callSkillWithProgress,
    cancelTask,
  }
}
