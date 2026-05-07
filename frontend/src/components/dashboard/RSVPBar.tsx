type Props = {
  confirmed: number
  pending: number
  declined: number
}

export function RSVPBar({ confirmed, pending, declined }: Props) {
  const total = confirmed + pending + declined
  if (total === 0) {
    return <div className="h-2 bg-[var(--color-cream)] rounded-full" />
  }

  const pctConfirmed = (confirmed / total) * 100
  const pctPending = (pending / total) * 100
  const pctDeclined = (declined / total) * 100

  return (
    <div className="flex h-2 rounded-full overflow-hidden bg-[var(--color-cream)]">
      {confirmed > 0 && (
        <div
          className="bg-[var(--color-rose)]"
          style={{ width: `${pctConfirmed}%` }}
          title={`Confirmed: ${confirmed}`}
        />
      )}
      {pending > 0 && (
        <div
          className="bg-amber-300"
          style={{ width: `${pctPending}%` }}
          title={`Pending: ${pending}`}
        />
      )}
      {declined > 0 && (
        <div
          className="bg-stone-400"
          style={{ width: `${pctDeclined}%` }}
          title={`Declined: ${declined}`}
        />
      )}
    </div>
  )
}
