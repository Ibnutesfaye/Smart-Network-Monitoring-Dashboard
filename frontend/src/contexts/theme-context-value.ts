import { createContext, useContext } from 'react'

export type Theme = 'dark' | 'light'

export const ThemeContext = createContext<{ theme: Theme; toggle: () => void } | null>(null)

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}
