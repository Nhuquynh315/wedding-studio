import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { daysUntil } from './dates'

describe('daysUntil', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-15T12:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns null for null input', () => {
    expect(daysUntil(null)).toBe(null)
    expect(daysUntil(undefined)).toBe(null)
  })

  it('returns null for invalid date string', () => {
    expect(daysUntil('not-a-date')).toBe(null)
  })

  it('returns positive days for future date', () => {
    expect(daysUntil('2026-06-20')).toBe(5)
  })

  it('returns 0 for today', () => {
    expect(daysUntil('2026-06-15')).toBe(0)
  })

  it('returns negative for past date', () => {
    expect(daysUntil('2026-06-10')).toBe(-5)
  })
})
