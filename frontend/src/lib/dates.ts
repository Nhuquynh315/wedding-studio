export function daysUntil(dateString: string | null | undefined): number | null {
  if (!dateString) return null
  const target = new Date(dateString)
  if (isNaN(target.getTime())) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  target.setHours(0, 0, 0, 0)
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}
