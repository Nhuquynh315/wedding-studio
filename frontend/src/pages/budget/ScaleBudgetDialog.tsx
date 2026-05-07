import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { TrendingUp } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { formatAUD } from '@/lib/format'

type Props = {
  weddingId: number
  currentTotal: number
  categoryCount: number
}

export function ScaleBudgetDialog({ weddingId, currentTotal, categoryCount }: Props) {
  const [open, setOpen] = useState(false)
  const [newTotalStr, setNewTotalStr] = useState('')
  const [error, setError] = useState<string | null>(null)
  const qc = useQueryClient()

  const newTotal = Number(newTotalStr)
  const ratio = currentTotal > 0 ? newTotal / currentTotal : 0
  const isValid = newTotalStr !== '' && !isNaN(newTotal) && newTotal > 0

  const mutation = useMutation({
    mutationFn: () => api.budget.scale(weddingId, { new_total: newTotal }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.budget.all(weddingId) })
      qc.invalidateQueries({ queryKey: queryKeys.weddings.all() })
      setOpen(false)
      setNewTotalStr('')
      setError(null)
    },
    onError: (err) => {
      setError(
        err instanceof ApiError
          ? err.problem.detail || err.problem.title
          : 'Something went wrong',
      )
    },
  })

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (!o) {
          setNewTotalStr('')
          setError(null)
        }
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={categoryCount === 0}>
          <TrendingUp className="h-4 w-4 mr-1" />
          Scale total
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Scale total budget</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <p className="text-sm text-[var(--color-text-muted)]">
            Current total allocated: <strong>{formatAUD(currentTotal)}</strong> across{' '}
            {categoryCount} categor{categoryCount === 1 ? 'y' : 'ies'}.
          </p>

          <div className="space-y-2">
            <Label htmlFor="new_total">New total (AUD)</Label>
            <Input
              id="new_total"
              type="number"
              min="0"
              step="100"
              value={newTotalStr}
              onChange={(e) => setNewTotalStr(e.target.value)}
              placeholder="30000"
              autoFocus
            />
          </div>

          {isValid && currentTotal > 0 && (
            <div className="text-sm bg-[var(--color-cream)] rounded p-3">
              <p className="font-medium mb-1">{ratio.toFixed(2)}× scaling factor</p>
              <p className="text-xs text-[var(--color-text-muted)]">
                Every category's allocation will be multiplied by this ratio. (E.g., a $10,000
                venue allocation becomes {formatAUD(10000 * ratio)}.)
              </p>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2"
            >
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={mutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              disabled={!isValid || mutation.isPending}
              className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
            >
              {mutation.isPending ? 'Scaling…' : 'Apply'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
