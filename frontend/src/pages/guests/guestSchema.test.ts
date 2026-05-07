import { describe, expect, it } from 'vitest'
import { guestSchema, formToPayload } from './guestSchema'

describe('guestSchema', () => {
  it('rejects missing full_name', () => {
    const result = guestSchema.safeParse({
      full_name: '',
      rsvp_status: 'pending',
    })
    expect(result.success).toBe(false)
  })

  it('rejects invalid email', () => {
    const result = guestSchema.safeParse({
      full_name: 'Alice',
      email: 'not-an-email',
      rsvp_status: 'pending',
    })
    expect(result.success).toBe(false)
  })

  it('accepts empty email (optional)', () => {
    const result = guestSchema.safeParse({
      full_name: 'Alice',
      email: '',
      rsvp_status: 'pending',
    })
    expect(result.success).toBe(true)
  })

  it('accepts valid input', () => {
    const result = guestSchema.safeParse({
      full_name: 'Alice Smith',
      email: 'alice@example.com',
      phone: '+61400111222',
      group_name: 'Smith Family',
      meal_preference: 'vegetarian',
      rsvp_status: 'confirmed',
    })
    expect(result.success).toBe(true)
  })
})

describe('formToPayload', () => {
  it('converts empty strings to null', () => {
    const payload = formToPayload({
      full_name: 'Alice',
      email: '',
      phone: '',
      group_name: '',
      meal_preference: '',
      rsvp_status: 'pending',
    })
    expect(payload.email).toBe(null)
    expect(payload.phone).toBe(null)
  })

  it('preserves trimmed values', () => {
    const payload = formToPayload({
      full_name: '  Alice  ',
      email: 'alice@example.com',
      phone: '',
      group_name: '',
      meal_preference: '',
      rsvp_status: 'pending',
    })
    expect(payload.full_name).toBe('Alice')
  })
})
