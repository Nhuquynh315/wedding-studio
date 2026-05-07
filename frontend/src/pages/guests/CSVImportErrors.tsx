type RowError = {
  row: number
  errors: Record<string, string[]>
}

type Props = {
  message?: string
  rowErrors: RowError[]
}

export function CSVImportErrors({ message, rowErrors }: Props) {
  if (rowErrors.length === 0) {
    return (
      <div
        role="alert"
        className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3"
      >
        {message || 'Import failed.'}
      </div>
    )
  }

  return (
    <div className="text-sm">
      <div
        role="alert"
        className="text-red-700 bg-red-50 border border-red-200 rounded p-3 mb-3"
      >
        <strong>Import failed.</strong> {rowErrors.length} row
        {rowErrors.length !== 1 ? 's' : ''} had errors. No guests were imported.
      </div>
      <div className="max-h-60 overflow-y-auto border border-[var(--color-border-default)] rounded">
        <table className="w-full">
          <thead className="bg-[var(--color-cream)] sticky top-0">
            <tr className="text-left text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
              <th className="px-3 py-2 w-16">Row</th>
              <th className="px-3 py-2">Error</th>
            </tr>
          </thead>
          <tbody>
            {rowErrors.map((re) => (
              <tr key={re.row} className="border-t border-[var(--color-border-default)]">
                <td className="px-3 py-2 font-mono text-xs align-top">{re.row}</td>
                <td className="px-3 py-2">
                  {Object.entries(re.errors).map(([field, msgs]) => (
                    <div key={field} className="text-xs">
                      <span className="font-medium">{field}:</span>{' '}
                      <span className="text-[var(--color-text-muted)]">{msgs.join(', ')}</span>
                    </div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
