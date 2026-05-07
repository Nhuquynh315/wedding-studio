import { BrowserRouter, Routes, Route } from 'react-router-dom'

import { AppLayout } from '@/components/layout/AppLayout'
import { AuthExpiredHandler } from '@/components/AuthExpiredHandler'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { DashboardPage } from '@/pages/DashboardPage'
import { BudgetPage } from '@/pages/budget/BudgetPage'
import { GuestsPage } from '@/pages/guests/GuestsPage'
import { VendorsPage } from '@/pages/vendors/VendorsPage'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { RegisterPage } from '@/pages/RegisterPage'

function PlaceholderPage({ name }: { name: string }) {
  return (
    <div className="p-8">
      <h1 className="font-serif text-3xl mb-2">{name}</h1>
      <p className="text-sm text-[var(--color-text-muted)]">Coming in a later prompt.</p>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthExpiredHandler />
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected — all share the AppLayout shell */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/guests" element={<GuestsPage />} />
          <Route path="/seating" element={<PlaceholderPage name="Seating" />} />
          <Route path="/budget" element={<BudgetPage />} />
          <Route path="/vendors" element={<VendorsPage />} />
          <Route path="/checklist" element={<PlaceholderPage name="Checklist" />} />
          <Route path="/settings" element={<PlaceholderPage name="Settings" />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
