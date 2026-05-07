import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { BudgetCategoryPublic } from '@/lib/api-schemas'
import { formatAUD } from '@/lib/format'

const FALLBACK_COLORS = [
  '#c9687a',
  '#e8a87c',
  '#7cb8e8',
  '#a8d8a8',
  '#d4a8d8',
  '#f0d4a8',
  '#a8c8d8',
  '#d8c8a8',
]

type Props = { categories: BudgetCategoryPublic[] }

export function BudgetDonut({ categories }: Props) {
  const data = categories
    .filter((c) => (c.allocated_amount ?? 0) > 0)
    .map((c, i) => ({
      name: c.name,
      value: c.allocated_amount ?? 0,
      color: c.color || FALLBACK_COLORS[i % FALLBACK_COLORS.length],
    }))

  if (data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-sm text-[var(--color-text-muted)]">
        No allocations yet
      </div>
    )
  }

  return (
    <div className="h-64">
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={90}
            paddingAngle={1}
            dataKey="value"
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => formatAUD(value)} />
          <Legend
            verticalAlign="bottom"
            iconSize={10}
            formatter={(value) => <span className="text-xs">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
