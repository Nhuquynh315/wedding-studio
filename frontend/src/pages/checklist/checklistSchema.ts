import { z } from 'zod'

export const CHECKLIST_CATEGORIES = [
  'Venue',
  'Catering',
  'Attire',
  'Photography',
  'Flowers',
  'Music',
  'Stationery',
  'Transport',
  'Honeymoon',
  'Other',
] as const

export const CHECKLIST_PRIORITIES = ['low', 'medium', 'high'] as const

export const checklistSchema = z.object({
  title: z.string().min(1, 'Required').max(300),
  category: z.enum(CHECKLIST_CATEGORIES),
  priority: z.enum(CHECKLIST_PRIORITIES),
  due_date: z.string().optional().or(z.literal('')),
  notes: z.string().optional().or(z.literal('')),
  is_completed: z.boolean(),
})

export type ChecklistFormValues = z.infer<typeof checklistSchema>

export function checklistToPayload(values: ChecklistFormValues) {
  const blank = (s: string | undefined) => (s && s.trim() ? s.trim() : null)
  return {
    title: values.title.trim(),
    category: values.category,
    priority: values.priority,
    due_date: blank(values.due_date),
    notes: blank(values.notes),
    is_completed: values.is_completed,
  }
}
