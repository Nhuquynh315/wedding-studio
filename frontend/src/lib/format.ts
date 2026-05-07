export function formatAUD(amount: number, opts?: { compact?: boolean }): string {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: opts?.compact ? 0 : 2,
    notation: opts?.compact ? 'compact' : 'standard',
  }).format(amount)
}
