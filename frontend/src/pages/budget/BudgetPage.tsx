import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { formatAUD } from '@/lib/format'
import { BudgetDonut } from '@/pages/budget/BudgetDonut'
import { CategoryDialog } from '@/pages/budget/CategoryDialog'
import { CategoryList } from '@/pages/budget/CategoryList'
import { DeleteCategoryDialog } from '@/pages/budget/DeleteCategoryDialog'
import { DeleteExpenseDialog } from '@/pages/budget/DeleteExpenseDialog'
import { ExpenseDialog } from '@/pages/budget/ExpenseDialog'
import { ExpenseList } from '@/pages/budget/ExpenseList'
import { ScaleBudgetDialog } from '@/pages/budget/ScaleBudgetDialog'
import type { BudgetCategoryPublic, ExpensePublic } from '@/lib/api-schemas'

export function BudgetPage() {
  const { activeId, isLoading: weddingsLoading } = useActiveWedding()
  const [editingCat, setEditingCat] = useState<BudgetCategoryPublic | null>(null)
  const [deletingCat, setDeletingCat] = useState<BudgetCategoryPublic | null>(null)
  const [editingExp, setEditingExp] = useState<ExpensePublic | null>(null)
  const [deletingExp, setDeletingExp] = useState<ExpensePublic | null>(null)

  const categoriesQuery = useQuery({
    queryKey: queryKeys.budget.categories(activeId ?? -1),
    queryFn: () => api.budget.listCategories(activeId!),
    enabled: !!activeId,
  })
  const expensesQuery = useQuery({
    queryKey: queryKeys.budget.expenses(activeId ?? -1),
    queryFn: () => api.budget.listExpenses(activeId!),
    enabled: !!activeId,
  })
  const summaryQuery = useQuery({
    queryKey: queryKeys.budget.summary(activeId ?? -1),
    queryFn: () => api.budget.summary(activeId!),
    enabled: !!activeId,
  })

  if (weddingsLoading || !activeId) {
    return (
      <div className="p-8">
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (categoriesQuery.isLoading || expensesQuery.isLoading || summaryQuery.isLoading) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        <Skeleton className="h-8 w-32 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
        <Skeleton className="h-48" />
      </div>
    )
  }

  const categories = categoriesQuery.data ?? []
  const expenses = expensesQuery.data ?? []
  const summary = summaryQuery.data
  const totalAllocated = summary?.total_allocated ?? 0
  const totalSpent = summary?.total_spent ?? 0

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-serif text-3xl mb-1">Budget</h1>
          <p className="text-sm text-[var(--color-text-muted)]">
            <strong>{formatAUD(totalSpent)}</strong> spent of{' '}
            <strong>{formatAUD(totalAllocated)}</strong> allocated
          </p>
        </div>
        <div className="flex gap-2">
          <ScaleBudgetDialog
            weddingId={activeId}
            currentTotal={totalAllocated}
            categoryCount={categories.length}
          />
          <CategoryDialog
            weddingId={activeId}
            trigger={
              <Button className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white">
                <Plus className="h-4 w-4 mr-1" />
                Category
              </Button>
            }
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardContent className="p-4">
            <h2 className="text-sm font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
              Allocation
            </h2>
            <BudgetDonut categories={categories} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <h2 className="text-sm font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-3">
              Categories
            </h2>
            {categories.length === 0 ? (
              <p className="text-sm text-[var(--color-text-muted)] py-4">
                No categories yet. Add one to start.
              </p>
            ) : (
              <CategoryList
                categories={categories}
                summary={summary}
                onEdit={setEditingCat}
                onDelete={setDeletingCat}
              />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
              Expenses
            </h2>
            <ExpenseDialog
              weddingId={activeId}
              categories={categories}
              trigger={
                <Button variant="outline" size="sm" disabled={categories.length === 0}>
                  <Plus className="h-4 w-4 mr-1" />
                  Expense
                </Button>
              }
            />
          </div>
          <ExpenseList
            expenses={expenses}
            categories={categories}
            onEdit={setEditingExp}
            onDelete={setDeletingExp}
          />
        </CardContent>
      </Card>

      <CategoryDialog
        weddingId={activeId}
        category={editingCat}
        onClose={() => setEditingCat(null)}
      />
      <DeleteCategoryDialog
        weddingId={activeId}
        category={deletingCat}
        onClose={() => setDeletingCat(null)}
      />
      <ExpenseDialog
        weddingId={activeId}
        categories={categories}
        expense={editingExp}
        onClose={() => setEditingExp(null)}
      />
      <DeleteExpenseDialog
        weddingId={activeId}
        expense={deletingExp}
        onClose={() => setDeletingExp(null)}
      />
    </div>
  )
}
