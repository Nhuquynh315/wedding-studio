import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { ChecklistForm } from '@/pages/checklist/ChecklistForm'
import { checklistToPayload } from '@/pages/checklist/checklistSchema'

export function AddItemDialog({ weddingId }: { weddingId: number }) {
  const [open, setOpen] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (payload: ReturnType<typeof checklistToPayload>) =>
      api.checklist.create(weddingId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.checklist.all(weddingId) })
      setOpen(false)
      setSubmitError(null)
    },
    onError: (err) => {
      setSubmitError(
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
        if (!o) setSubmitError(null)
      }}
    >
      <DialogTrigger asChild>
        <Button className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white">
          <Plus className="h-4 w-4 mr-1" />
          Item
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Add checklist item</DialogTitle>
        </DialogHeader>
        {submitError && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {submitError}
          </div>
        )}
        <ChecklistForm
          onSubmit={async (payload) => mutation.mutate(payload)}
          onCancel={() => setOpen(false)}
          submitLabel="Add item"
          isSubmitting={mutation.isPending}
        />
      </DialogContent>
    </Dialog>
  )
}
