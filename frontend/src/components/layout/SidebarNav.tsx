import { NavLink } from 'react-router-dom'
import { NAV_ITEMS } from '@/components/layout/nav-config'
import { cn } from '@/lib/utils'

type Props = {
  onNavigate?: () => void
}

export function SidebarNav({ onNavigate }: Props) {
  return (
    <nav className="flex flex-col gap-1 px-3 py-4">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[var(--color-rose-bg)] text-[var(--color-rose-dark)]'
                  : 'text-[var(--color-text-dark)] hover:bg-[var(--color-cream)]',
              )
            }
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        )
      })}
    </nav>
  )
}
