import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 100))
    expect(result.current).toBe('hello')
  })

  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 100),
      { initialProps: { value: 'a' } },
    )

    expect(result.current).toBe('a')

    rerender({ value: 'ab' })
    expect(result.current).toBe('a') // not yet updated

    rerender({ value: 'abc' })
    expect(result.current).toBe('a') // still not updated; timer reset

    act(() => { vi.advanceTimersByTime(99) })
    expect(result.current).toBe('a') // 1ms before delay; still not

    act(() => { vi.advanceTimersByTime(2) })
    expect(result.current).toBe('abc') // delay elapsed; updated
  })
})
