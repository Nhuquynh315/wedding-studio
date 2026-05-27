import {
  Calendar,
  CheckSquare,
  DollarSign,
  LayoutDashboard,
  Settings,
  Sparkles,
  Users,
  Utensils,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type NavItem = {
  label: string
  to: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: LayoutDashboard },
  { label: 'Guests', to: '/guests', icon: Users },
  { label: 'Seating', to: '/seating', icon: Utensils },
  { label: 'Budget', to: '/budget', icon: DollarSign },
  { label: 'Vendors', to: '/vendors', icon: Calendar },
  { label: 'Checklist', to: '/checklist', icon: CheckSquare },
  { label: 'Invitations', to: '/invitations', icon: Sparkles },
  { label: 'Settings', to: '/settings', icon: Settings },
]
