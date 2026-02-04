import { useState, useEffect } from 'react'
import { Slider } from '@radix-ui/react-slider'
import { Label } from '@radix-ui/react-label'
import { cn } from '@/lib/utils'

export interface ParameterInputProps {
  label: string
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
  unit?: string
  description?: string
}

export function ParameterInput({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 0.1,
  unit = '',
  description = '',
}: ParameterInputProps) {
  const [localValue, setLocalValue] = useState(value)

  useEffect(() => {
    setLocalValue(value)
  }, [value])

  const handleChange = (newValue: number[]) => {
    const value = newValue[0]
    setLocalValue(value)
    onChange(value)
  }

  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <Label htmlFor={label}>{label}</Label>
          <span className="text-sm text-muted-foreground">
            {localValue.toFixed(2)} {unit}
          </span>
        </div>
        <Slider.Root
          id={label}
          min={min}
          max={max}
          step={step}
          value={[localValue]}
          onValueChange={handleChange}
          className="flex-1"
        >
          <Slider.Track className="h-2 w-full grow relative rounded-full bg-secondary">
            <Slider.Range className="absolute h-full bg-primary" />
          </Slider.Track>
          <Slider.Thumb className="block w-5 h-5 rounded-full border-2 border-primary bg-background shadow focus:outline-none focus:ring-2 focus:ring-slate-950 disabled:pointer-events-none" />
        </Slider.Root>
      </div>
      {description && (
        <p className="text-xs text-muted-foreground">
          {description}
        </p>
      )}
    </div>
  )
}
