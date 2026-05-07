import { useRef, useState } from 'react'
import { Upload, X } from 'lucide-react'
import { cn } from '@/lib/utils'

const MAX_SIZE_BYTES = 1024 * 1024 // 1 MB, matches backend

type Props = {
  file: File | null
  onChange: (file: File | null) => void
  onError: (message: string | null) => void
}

export function FileDropZone({ file, onChange, onError }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const validate = (f: File): string | null => {
    if (!f.name.toLowerCase().endsWith('.csv')) return 'File must be a .csv'
    if (f.size > MAX_SIZE_BYTES)
      return `File too large (${Math.round(f.size / 1024)} KB; max 1024 KB)`
    return null
  }

  const handleFile = (f: File | null) => {
    if (!f) {
      onChange(null)
      onError(null)
      return
    }
    const err = validate(f)
    if (err) {
      onChange(null)
      onError(err)
      return
    }
    onChange(f)
    onError(null)
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          const dropped = e.dataTransfer.files[0]
          if (dropped) handleFile(dropped)
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragging
            ? 'border-[var(--color-rose)] bg-[var(--color-rose-bg)]'
            : 'border-[var(--color-border-default)] hover:border-[var(--color-rose)]',
        )}
      >
        <Upload className="h-10 w-10 mx-auto mb-3 text-[var(--color-text-muted)]" />
        {file ? (
          <div className="flex items-center justify-center gap-2">
            <span className="text-sm font-medium">{file.name}</span>
            <span className="text-xs text-[var(--color-text-muted)]">
              ({Math.round(file.size / 1024)} KB)
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleFile(null)
              }}
              className="p-1 rounded hover:bg-white"
              aria-label="Remove file"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <p className="text-sm font-medium mb-1">Drop a CSV here, or click to choose</p>
            <p className="text-xs text-[var(--color-text-muted)]">Max 1 MB. Header row required.</p>
          </>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
      />
    </div>
  )
}
