import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

export function useUrlState(key: string): [string | null, (v: string | null) => void] {
  const [params, setParams] = useSearchParams()
  const value = params.get(key)

  const setValue = useCallback(
    (newValue: string | null) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          if (newValue === null || newValue === '') {
            next.delete(key)
          } else {
            next.set(key, newValue)
          }
          return next
        },
        { replace: true },
      )
    },
    [key, setParams],
  )

  return [value, setValue]
}
