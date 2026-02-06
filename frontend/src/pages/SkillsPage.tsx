
import { useState, useEffect } from 'react'
import { Wrench, CheckCircle, Info, Loader2 } from 'lucide-react'

interface SkillMethod {
  name: string
  description: string
  parameters: string[]
}

interface SkillModule {
  name: string
  description: string
  methods: string[] | Record<string, SkillMethod> // Backend returns list of strings for methods currently, or dict?
}

// Based on backend/api/skill_calls.py:
// modules = { "airfoil_library": { "name": "...", "description": "...", "methods": ["..."] } }
// So methods is string[]

interface SkillModuleData {
  name: string
  description: string
  methods: string[]
}

export function SkillsPage() {
  const [skills, setSkills] = useState<Record<string, SkillModuleData>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const res = await fetch('/api/skill/modules')
        if (res.ok) {
          const data = await res.json()
          if (data.success) {
            setSkills(data.modules)
          } else {
            setError('Failed to load skills')
          }
        } else {
          setError(`HTTP Error: ${res.status}`)
        }
      } catch (e) {
        setError('Failed to fetch skills')
        console.error(e)
      } finally {
        setLoading(false)
      }
    }

    fetchSkills()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-10 text-center text-red-500">
        <p>Error loading skills: {error}</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Wrench className="w-8 h-8" />
          Skills & MCP Tools
        </h1>
      </div>

      <div className="bg-card rounded-lg border shadow-sm p-6">
        <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 p-4 rounded-md flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold text-blue-700 dark:text-blue-300">MCP (Model Context Protocol) Integration</p>
            <p className="text-blue-600 dark:text-blue-400 mt-1">
              The tools listed below are exposed to the AI Agent via the backend. The Agent autonomously decides when to use them based on your conversation.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {Object.entries(skills).map(([id, skill]: [string, SkillModuleData]) => (
            <div key={id} className="border rounded-lg p-4 flex items-start justify-between bg-card hover:bg-accent/50 transition-colors">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-lg">{skill.name}</h3>
                  <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-0.5 rounded-full">
                    <CheckCircle className="w-3 h-3" />
                    Active
                  </span>
                </div>
                <p className="text-muted-foreground text-sm mb-3">{skill.description}</p>
                <div className="flex flex-wrap gap-2">
                  {skill.methods.map(method => (
                    <span key={method} className="text-xs font-mono bg-secondary px-2 py-1 rounded text-secondary-foreground">
                      {method}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
