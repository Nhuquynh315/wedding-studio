import type { WeddingPublic } from '@/lib/api-schemas'

type Props = {
  weddings: WeddingPublic[]
  activeId: number | null
  onChange: (id: number) => void
}

export function WeddingSelector({ weddings, activeId, onChange }: Props) {
  if (weddings.length === 1) {
    const w = weddings[0]
    return (
      <h2 className="font-serif text-2xl">
        {w.partner1_name} & {w.partner2_name}
      </h2>
    )
  }

  return (
    <select
      value={activeId ?? ''}
      onChange={(e) => onChange(parseInt(e.target.value, 10))}
      className="font-serif text-2xl bg-transparent border-b border-[var(--color-border-default)] focus:outline-none focus:border-[var(--color-rose)]"
    >
      {weddings.map((w) => (
        <option key={w.id} value={w.id}>
          {w.partner1_name} & {w.partner2_name}
        </option>
      ))}
    </select>
  )
}
