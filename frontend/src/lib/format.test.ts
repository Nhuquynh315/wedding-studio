import { describe, expect, it } from 'vitest'
import { formatAUD } from './format'

describe('formatAUD', () => {
  it('formats whole numbers', () => {
    const result = formatAUD(1000)
    expect(result).toContain('1,000')
    expect(result).toContain('$')
  })

  it('handles zero', () => {
    expect(formatAUD(0)).toContain('0')
  })

  it('formats large numbers', () => {
    expect(formatAUD(30000)).toContain('30,000')
  })

  it('compact mode shortens', () => {
    const compact = formatAUD(30000, { compact: true })
    const standard = formatAUD(30000)
    expect(compact.length).toBeLessThan(standard.length)
  })
})
