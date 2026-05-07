import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { VendorForm } from '@/pages/vendors/VendorForm'
import { vendorToPayload } from '@/pages/vendors/vendorSchema'

export function AddVendorDialog({ weddingId }: { weddingId: number }) {
  const [open, setOpen] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (payload: ReturnType<typeof vendorToPayload>) =>
      api.vendors.create(weddingId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vendors.all(weddingId) })
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
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) setSubmitError(null) }}>
      <DialogTrigger asChild>
        <Button className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white">
          <Plus className="h-4 w-4 mr-1" />
          Vendor
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Add vendor</DialogTitle>
        </DialogHeader>
        {submitError && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {submitError}
          </div>
        )}
        <VendorForm
          onSubmit={async (payload) => mutation.mutate(payload)}
          onCancel={() => setOpen(false)}
          submitLabel="Add vendor"
          isSubmitting={mutation.isPending}
        />
      </DialogContent>
    </Dialog>
  )
}
