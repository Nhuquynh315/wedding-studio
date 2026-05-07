import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

const SAMPLE_CSV = `full_name,email,phone,group_name,meal_preference,rsvp_status
Alice Smith,alice@example.com,+61400111222,Smith Family,vegetarian,confirmed
Bob Jones,,,,,pending`

export function CSVFormatHint() {
  const [open, setOpen] = useState(false)

  return (
    <div className="text-sm">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-[var(--color-rose)] hover:underline"
      >
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        CSV format
      </button>
      {open && (
        <div className="mt-2 p-3 bg-[var(--color-cream)] rounded text-xs">
          <p className="mb-2 text-[var(--color-text-muted)]">
            Header row required. <strong>full_name</strong> is required; other columns are
            optional.
          </p>
          <pre className="bg-white p-2 rounded border border-[var(--color-border-default)] overflow-x-auto">
            {SAMPLE_CSV}
          </pre>
          <p className="mt-2 text-[var(--color-text-muted)]">
            Recognized columns: full_name, email, phone, group_name, meal_preference, rsvp_status
            (pending/confirmed/declined). Extra columns are ignored. UTF-8 with or without BOM.
            All-or-nothing: any row error rejects the entire upload.
          </p>
        </div>
      )}
    </div>
  )
}
