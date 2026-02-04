import { useState, useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'


export interface ModeToggleProps {
  darkMode: boolean
  onToggle: (darkMode: boolean) => void
}

export function ModeToggle({ darkMode, onToggle }: ModeToggleProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <button
      onClick={() => onToggle(!darkMode)}
      className="relative inline-flex items-center justify-center rounded-md p-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-slate-950 disabled:opacity-50 disabled:pointer-events-none"
      aria-label="Toggle theme"
    >
      {mounted ? (
        <>
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <span className="sr-only">Use light mode</span>
        </>
      ) : (
        <>
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Use dark mode</span>
        </>
      )}
    </button>
  )
}
