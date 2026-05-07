import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { ChecklistForm } from '@/pages/checklist/ChecklistForm'
import { checklistToPayload } from '@/pages/checklist/checklistSchema'
import type { ChecklistItemPublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  item: ChecklistItemPublic | null
  onClose: () => void
}

export function EditItemDialog({ weddingId, item, onClose }: Props) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (payload: ReturnType<typeof checklistToPayload>) => {
      if (!item) throw new Error('No item')
      return api.checklist.update(weddingId, item.id, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.checklist.all(weddingId) })
      setSubmitError(null)
      onClose()
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
      open={!!item}
      onOpenChange={(o) => {
        if (!o) {
          setSubmitError(null)
          onClose()
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Edit item</DialogTitle>
        </DialogHeader>
        {submitError && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {submitError}
          </div>
        )}
        {item && (
          <ChecklistForm
            initial={item}
            onSubmit={async (payload) => mutation.mutate(payload)}
            onCancel={() => { setSubmitError(null); onClose() }}
            submitLabel="Save changes"
            isSubmitting={mutation.isPending}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
