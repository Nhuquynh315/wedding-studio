import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { VendorForm } from '@/pages/vendors/VendorForm'
import { vendorToPayload } from '@/pages/vendors/vendorSchema'
import type { VendorPublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  vendor: VendorPublic | null
  onClose: () => void
}

export function EditVendorDialog({ weddingId, vendor, onClose }: Props) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (payload: ReturnType<typeof vendorToPayload>) => {
      if (!vendor) throw new Error('No vendor')
      return api.vendors.update(weddingId, vendor.id, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vendors.all(weddingId) })
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
    <Dialog open={!!vendor} onOpenChange={(o) => { if (!o) { setSubmitError(null); onClose() } }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Edit vendor</DialogTitle>
        </DialogHeader>
        {submitError && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {submitError}
          </div>
        )}
        {vendor && (
          <VendorForm
            initial={vendor}
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
