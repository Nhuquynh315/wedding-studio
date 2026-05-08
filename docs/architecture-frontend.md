# Frontend Architecture — Phase 4

React + TypeScript SPA consuming the Phase 3 FastAPI JSON API.

## Stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | React 18 | Concurrent mode, `createRoot` |
| Language | TypeScript 5 | Strict mode (`"strict": true`) |
| Build tool | Vite 6 | Rolldown bundler in production |
| Routing | React Router v7 | `createBrowserRouter`, data-less loaders |
| Server state | TanStack Query v5 | `useQuery` / `useMutation` with `queryClient` |
| Forms | React Hook Form + Zod | Schema-first validation; errors shown inline |
| Styling | Tailwind CSS v4 | Utility-first; no CSS modules |
| UI primitives | Radix UI (hand-wrapped) | shadcn/New York style; see note below |
| Drag-and-drop | dnd-kit | Seating chart only |
| Charts | Recharts | Budget pie/bar charts |
| HTTP client | `fetch` wrapper | `src/lib/api.ts`; throws `ApiError` on non-2xx |
| Unit tests | Vitest + Testing Library | jsdom environment |
| E2E tests | Playwright | Auto-starts both servers via `webServer` |

**Radix UI note:** `npx shadcn@latest add` is blocked by a TypeScript 6 peer dep conflict
(shadcn's internal `npm install` fails). Components were installed by adding the Radix
packages directly (`npm install @radix-ui/react-* --legacy-peer-deps`) and hand-writing
the shadcn New York source. Components live in `src/components/ui/`.

## Project layout

```
frontend/src/
├── components/
│   ├── ui/           # shadcn-style primitives (Button, Input, Card, …)
│   ├── AuthGuard.tsx
│   ├── Layout.tsx    # sidebar + mobile top bar
│   └── QueryErrorState.tsx
├── hooks/
│   └── useActiveWedding.ts   # localStorage-backed active wedding ID
├── lib/
│   ├── api.ts        # fetch wrapper + resource helpers
│   ├── dates.ts      # daysUntil()
│   ├── query-keys.ts # centralised key factory
│   └── tokens.ts     # JWT storage helpers
├── pages/
│   ├── auth/         # LoginPage, RegisterPage
│   ├── dashboard/    # DashboardPage, CreateWeddingDialog
│   ├── guests/       # GuestsPage, GuestForm, dialogs
│   ├── budget/       # BudgetPage, CategoryForm, ExpenseForm, dialogs
│   ├── vendors/      # VendorsPage, VendorForm, dialogs
│   ├── checklist/    # ChecklistPage, ChecklistItemForm, dialogs
│   ├── seating/      # SeatingPage, drag-and-drop zone/chip components
│   └── settings/     # SettingsPage, WeddingListSection, dialogs
├── test/
│   └── setup.ts      # @testing-library/jest-dom matchers
└── main.tsx
```

## API integration

All HTTP traffic goes through `src/lib/api.ts`. The module:

1. Reads the JWT from `localStorage` via `src/lib/tokens.ts`
2. Attaches `Authorization: Bearer <token>` to every request
3. Throws `ApiError` (subclass of `Error`) for non-2xx responses, carrying `status` and the RFC 7807 `body` (`title`, `detail`)
4. Dispatches `AUTH_EXPIRED_EVENT` (a custom DOM event) when a 401 is received — `AuthGuard` listens for this and redirects to `/login`

The base URL is empty (same origin). In development Vite proxies `/api` to `http://localhost:8000` via `vite.config.ts`.

## State management

No global store. State is split into:

| Kind | Tool | Where |
|---|---|---|
| Server state | TanStack Query | All resource fetches and mutations |
| Form state | React Hook Form | Inside form components |
| Active wedding | `localStorage` | `useActiveWedding` hook + `ACTIVE_WEDDING_KEY` constant |
| Auth tokens | `localStorage` | `src/lib/tokens.ts` (`access_token`, `refresh_token`) |
| UI state | `useState` | Local to the component that owns it |

## Cache invalidation strategy

Every mutation's `onSuccess` (or `onSettled`) calls `queryClient.invalidateQueries` with the
affected key namespace. Key namespaces come from `src/lib/query-keys.ts`:

```ts
export const queryKeys = {
  weddings: { all: () => ['weddings'] },
  guests:   { list: (wid) => ['guests', wid], ... },
  budget:   { summary: (wid) => ['budget', 'summary', wid], ... },
  vendors:  { list: (wid) => ['vendors', wid], ... },
  checklist:{ list: (wid) => ['checklist', wid], ... },
  tables:   { withGuests: (wid) => ['tables', 'with-guests', wid], ... },
}
```

Mutations that affect multiple resources (e.g., assigning a guest to a table) invalidate
both keys.

## Optimistic updates

Used in two places where latency would cause visible lag:

**Checklist toggle** (`ChecklistPage`):
- `onMutate`: cancel in-flight queries → snapshot current list → write optimistic state
- `onError`: rollback to snapshot
- `onSettled`: invalidate to sync server truth

**Seating assignment** (`SeatingPage`):
- Same pattern; `with-guests` snapshot updated by moving guest between table buckets
- Rollback restores the snapshot on network error

## Component architecture

### Page → Section → Dialog pattern

Each page owns its data fetching (`useQuery`). Dialogs receive mutation-specific props and
handle their own `useMutation` + form state. Confirmation dialogs (delete) are separate
components from edit dialogs.

### Dual-mode dialogs

`CreateWeddingDialog` works in two modes via a TypeScript discriminated union:

```ts
type Props =
  | { open: boolean; onClose: () => void; onCreated?: (id: number) => void; trigger?: never }
  | { trigger: ReactNode; onCreated?: (id: number) => void; open?: never; onClose?: never }
```

Trigger mode keeps its own `internalOpen` state; controlled mode is driven by the parent.

### Error display

`QueryErrorState` (`src/components/QueryErrorState.tsx`) provides consistent error UI
across all pages. It discriminates on `ApiError.status`:

- 401 → clears tokens, dispatches `AUTH_EXPIRED_EVENT`
- 403 → "Access denied"
- 404 → "We couldn't find {resourceName}"
- 5xx → "The server is having trouble"
- Non-`ApiError` (`instanceof Error`) → "Network problem"
- Includes a retry button that calls `refetch()`

## Form pattern

All forms use `react-hook-form` with a Zod schema resolver:

```ts
const schema = z.object({ title: z.string().min(1), ... })
const { register, handleSubmit, formState: { errors } } = useForm<z.infer<typeof schema>>({
  resolver: zodResolver(schema),
  defaultValues: ...
})
```

API errors (422 validation, 409 conflict) are mapped to form-level errors via
`setError('root', { message: body.detail })` and displayed below the submit button.

## Testing

### Unit tests (Vitest)

Config: `frontend/vitest.config.ts` (separate from `vite.config.ts`; jsdom environment).
`exclude: ['**/e2e/**']` prevents Playwright specs from being picked up.

Coverage targets: utility functions (`daysUntil`, `formatCurrency`), form validation
schemas (Zod), pure components. Integration tests mock `fetch` via `vi.stubGlobal`.

### E2E tests (Playwright)

Config: `frontend/playwright.config.ts`. Two `webServer` entries:

1. `uvicorn api.main:app --port 8000` — FastAPI backend
2. `vite --port 5173 --strictPort` — React dev server

`reuseExistingServer: !process.env.CI` so local dev re-uses running servers.

Specs live in `frontend/e2e/`. The full-flow spec (`full-flow.spec.ts`) covers:
register → create wedding → navigate to Guests → navigate to Budget.

Selectors are scoped to `page.locator('main')` to avoid collisions with the sidebar nav
(which duplicates page titles as link labels).

## Known gaps (Phase 5+)

- **No token refresh UI**: Expired tokens show a toast + redirect to login; silent refresh
  (using `refresh_token`) is not implemented
- **No pagination UI**: Guest list uses TanStack Query's `useInfiniteQuery` shape but the
  page renders all results; "load more" button is a Phase 5 item
- **Profile + Password sections**: `SettingsPage` renders placeholder sections; the
  `PATCH /api/v1/auth/me` and password-change endpoints are not yet wired up
- **No offline support**: PWA / service worker is out of scope
- **SQLite in production**: Phase 5 will migrate to PostgreSQL; no frontend impact expected
