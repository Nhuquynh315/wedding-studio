import { LogOut, Settings as SettingsIcon } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/lib/auth-context'

function getInitials(nameOrEmail: string): string {
  const parts = nameOrEmail.split(/[\s@]+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return parts[0]?.slice(0, 2).toUpperCase() ?? '??'
}

export function UserMenu() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  const initials = getInitials(user.full_name || user.email)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-3 px-3 py-2 rounded-md w-full hover:bg-[var(--color-cream)] transition-colors text-left">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-[var(--color-rose-bg)] text-[var(--color-rose-dark)] text-xs font-medium">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium truncate">
              {user.full_name || user.email}
            </div>
            {user.full_name && (
              <div className="text-xs text-[var(--color-text-muted)] truncate">
                {user.email}
              </div>
            )}
          </div>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>My Account</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate('/settings')}>
          <SettingsIcon className="mr-2 h-4 w-4" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuItem onClick={logout} className="text-red-600 focus:text-red-700">
          <LogOut className="mr-2 h-4 w-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
