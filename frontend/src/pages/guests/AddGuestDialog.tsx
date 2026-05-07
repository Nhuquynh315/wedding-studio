import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { GuestForm } from '@/pages/guests/GuestForm'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { GuestCreate } from '@/lib/api-schemas'

export function AddGuestDialog({ weddingId }: { weddingId: number }) {
  const [open, setOpen] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (payload: GuestCreate) => api.guests.create(weddingId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.guests.all(weddingId) })
      setOpen(false)
      setSubmitError(null)
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setSubmitError(err.problem.detail || err.problem.title)
      } else {
        setSubmitError('Something went wrong')
      }
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
          Add guest
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Add guest</DialogTitle>
        </DialogHeader>
        {submitError && (
          <div
            role="alert"
            className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-2"
          >
            {submitError}
          </div>
        )}
        <GuestForm
          onSubmit={(payload) => mutation.mutateAsync(payload as GuestCreate)}
          onCancel={() => setOpen(false)}
          submitLabel="Add guest"
          isSubmitting={mutation.isPending}
        />
      </DialogContent>
    </Dialog>
  )
}
