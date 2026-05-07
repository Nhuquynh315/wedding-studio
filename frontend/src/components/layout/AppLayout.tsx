import { useState } from 'react'
import { Menu } from 'lucide-react'
import { Outlet } from 'react-router-dom'

import { SidebarNav } from '@/components/layout/SidebarNav'
import { UserMenu } from '@/components/layout/UserMenu'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:flex-col w-64 border-r border-[var(--color-border-default)] bg-white">
        <div className="px-6 py-5 border-b border-[var(--color-border-default)]">
          <h1 className="font-serif text-xl text-[var(--color-text-dark)]">Wedding Studio</h1>
        </div>
        <div className="flex-1 overflow-y-auto">
          <SidebarNav />
        </div>
        <div className="border-t border-[var(--color-border-default)] p-3">
          <UserMenu />
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 flex items-center justify-between px-4 py-3 bg-white border-b border-[var(--color-border-default)]">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <button
              className="p-2 -ml-2 rounded-md hover:bg-[var(--color-cream)]"
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <div className="px-6 py-5 border-b border-[var(--color-border-default)]">
              <h1 className="font-serif text-xl">Wedding Studio</h1>
            </div>
            <SidebarNav onNavigate={() => setMobileOpen(false)} />
            <div className="border-t border-[var(--color-border-default)] p-3">
              <UserMenu />
            </div>
          </SheetContent>
        </Sheet>
        <h1 className="font-serif text-lg">Wedding Studio</h1>
        <div className="w-9" />
      </div>

      {/* Main content */}
      <main className="flex-1 md:ml-0 mt-14 md:mt-0">
        <Outlet />
      </main>
    </div>
  )
}
