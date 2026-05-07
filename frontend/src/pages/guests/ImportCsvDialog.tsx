import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Upload } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { CSVFormatHint } from '@/pages/guests/CSVFormatHint'
import { CSVImportErrors } from '@/pages/guests/CSVImportErrors'
import { FileDropZone } from '@/pages/guests/FileDropZone'

type Phase = 'upload' | 'success' | 'error'

type RowError = {
  row: number
  errors: Record<string, string[]>
}

export function ImportCsvDialog({ weddingId }: { weddingId: number }) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [clientError, setClientError] = useState<string | null>(null)
  const [phase, setPhase] = useState<Phase>('upload')
  const [importedCount, setImportedCount] = useState(0)
  const [serverErrorMessage, setServerErrorMessage] = useState<string | null>(null)
  const [rowErrors, setRowErrors] = useState<RowError[]>([])
  const qc = useQueryClient()

  const reset = () => {
    setFile(null)
    setClientError(null)
    setPhase('upload')
    setRowErrors([])
    setServerErrorMessage(null)
  }

  const mutation = useMutation({
    mutationFn: (f: File) => api.guests.importCsv(weddingId, f),
    onSuccess: (result) => {
      setImportedCount(result.imported)
      setPhase('success')
      qc.invalidateQueries({ queryKey: queryKeys.guests.all(weddingId) })
      setTimeout(() => {
        setOpen(false)
        reset()
      }, 2000)
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        const rows = (err.problem.row_errors as RowError[] | undefined) ?? []
        setRowErrors(rows)
        setServerErrorMessage(err.problem.detail || err.problem.title)
        setPhase('error')
      } else {
        setServerErrorMessage('Network error')
        setPhase('error')
      }
    },
  })

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (!o) reset()
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline">
          <Upload className="h-4 w-4 mr-1" />
          Import CSV
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Import guests from CSV</DialogTitle>
        </DialogHeader>

        {phase === 'upload' && (
          <div className="space-y-4">
            <CSVFormatHint />
            <FileDropZone file={file} onChange={setFile} onError={setClientError} />
            {clientError && (
              <div
                role="alert"
                className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2"
              >
                {clientError}
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setOpen(false)
                  reset()
                }}
                disabled={mutation.isPending}
              >
                Cancel
              </Button>
              <Button
                onClick={() => file && mutation.mutate(file)}
                disabled={!file || mutation.isPending}
                className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
              >
                {mutation.isPending ? 'Importing…' : 'Import'}
              </Button>
            </div>
          </div>
        )}

        {phase === 'success' && (
          <div className="py-6 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto mb-3" />
            <p className="font-medium">
              {importedCount} guest{importedCount !== 1 ? 's' : ''} imported
            </p>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">Closing in a moment…</p>
          </div>
        )}

        {phase === 'error' && (
          <div className="space-y-4">
            <CSVImportErrors
              message={serverErrorMessage ?? undefined}
              rowErrors={rowErrors}
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={reset}>
                Choose different file
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setOpen(false)
                  reset()
                }}
              >
                Close
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
