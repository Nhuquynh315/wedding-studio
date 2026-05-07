import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { GuestForm } from '@/pages/guests/GuestForm'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { GuestPublic, GuestUpdate } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  guest: GuestPublic | null
  onClose: () => void
}

export function EditGuestDialog({ weddingId, guest, onClose }: Props) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (payload: GuestUpdate) => {
      if (!guest) throw new Error('No guest to update')
      return api.guests.update(weddingId, guest.id, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.guests.all(weddingId) })
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
    <Dialog open={!!guest} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Edit guest</DialogTitle>
        </DialogHeader>
        {submitError && (
          <div
            role="alert"
            className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-2"
          >
            {submitError}
          </div>
        )}
        {guest && (
          <GuestForm
            initial={guest}
            onSubmit={(payload) => mutation.mutateAsync(payload as GuestUpdate)}
            onCancel={onClose}
            submitLabel="Save changes"
            isSubmitting={mutation.isPending}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
