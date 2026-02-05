
import { useState } from 'react'
import { Wrench, CheckCircle, Info } from 'lucide-react'

export function SkillsPage() {
  const [skills] = useState([
    {
      id: 'atmosphere',
      name: 'Standard Atmosphere',
      description: 'Calculates standard atmosphere properties (temperature, pressure, density) at a given altitude.',
      enabled: true,
      parameters: ['altitude_m', 'temp_offset_c']
    },
    {
      id: 'lift_slope',
      name: 'Lift Slope Calculator',
      description: 'Calculates the subsonic lift slope of a wing based on geometry (aspect ratio, sweep).',
      enabled: true,
      parameters: ['aspect_ratio', 'sweep_quarter_chord_deg', 'mach']
    }
  ])

  return (
    <div className="container mx-auto p-6 max-w-4xl">
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
          {skills.map(skill => (
            <div key={skill.id} className="border rounded-lg p-4 flex items-start justify-between bg-card hover:bg-accent/50 transition-colors">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-lg">{skill.name}</h3>
                  {skill.enabled && (
                    <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-0.5 rounded-full">
                      <CheckCircle className="w-3 h-3" />
                      Active
                    </span>
                  )}
                </div>
                <p className="text-muted-foreground text-sm mb-3">{skill.description}</p>
                <div className="flex flex-wrap gap-2">
                  {skill.parameters.map(param => (
                    <span key={param} className="text-xs font-mono bg-secondary px-2 py-1 rounded text-secondary-foreground">
                      {param}
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
