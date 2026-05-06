import { tokens } from '@/lib/tokens'
import type * as Schema from '@/lib/api-schemas'

const API_BASE = '/api/v1'

// ── Errors ──────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    public problem: Schema.ProblemDetails,
  ) {
    super(problem.detail || problem.title)
    this.name = 'ApiError'
  }
}

// ── Auth-expired event (handled by router in Prompt 4) ──────────

export const AUTH_EXPIRED_EVENT = 'auth:expired'

function emitAuthExpired() {
  window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
}

// ── Refresh-token deduplication ─────────────────────────────────

// If multiple requests 401 at once, exactly ONE refresh goes out;
// the others wait on this in-flight promise.
let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokens.getRefresh()
  if (!refresh) return null

  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    try {
      const resp = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      })
      if (!resp.ok) {
        tokens.clear()
        emitAuthExpired()
        return null
      }
      const data = (await resp.json()) as Schema.Token
      tokens.set(data.access_token, data.refresh_token)
      return data.access_token
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

// ── Core fetch wrapper ──────────────────────────────────────────

type FetchOptions = {
  method?: string
  body?: unknown
  formData?: FormData
  query?: Record<string, string | number | boolean | undefined | null>
  skipAuth?: boolean
}

async function request<T>(
  path: string,
  options: FetchOptions = {},
  _isRetry = false,
): Promise<T> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin)
  if (options.query) {
    for (const [key, value] of Object.entries(options.query)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const headers: Record<string, string> = {}
  if (!options.skipAuth) {
    const access = tokens.getAccess()
    if (access) headers['Authorization'] = `Bearer ${access}`
  }

  let body: BodyInit | undefined
  if (options.formData) {
    body = options.formData
    // DO NOT set Content-Type — browser sets multipart boundary automatically
  } else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body)
  }

  const resp = await fetch(url.toString(), {
    method: options.method || 'GET',
    headers,
    body,
  })

  if (resp.status === 204) return undefined as T

  if (resp.status === 401 && !options.skipAuth && !_isRetry) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      return request<T>(path, options, true)
    }
    // refresh failed; emitAuthExpired already fired inside refreshAccessToken
  }

  const contentType = resp.headers.get('content-type') ?? ''
  const data = contentType.includes('json')
    ? await resp.json()
    : await resp.text()

  if (!resp.ok) {
    const problem = (
      typeof data === 'object' && data !== null
        ? data
        : { type: 'about:blank', title: resp.statusText, status: resp.status }
    ) as Schema.ProblemDetails
    throw new ApiError(resp.status, problem)
  }

  return data as T
}

// ── Typed namespaced client ─────────────────────────────────────

export const api = {
  auth: {
    register: (body: Schema.UserCreate) =>
      request<Schema.UserPublic>('/auth/register', { method: 'POST', body, skipAuth: true }),
    login: (body: Schema.UserLogin) =>
      request<Schema.Token>('/auth/login', { method: 'POST', body, skipAuth: true }),
    me: () => request<Schema.UserPublic>('/auth/me'),
    logout: () => {
      tokens.clear()
    },
  },

  weddings: {
    list: () => request<Schema.WeddingPublic[]>('/weddings'),
    get: (id: number) => request<Schema.WeddingPublic>(`/weddings/${id}`),
    create: (body: Schema.WeddingCreate) =>
      request<Schema.WeddingPublic>('/weddings', { method: 'POST', body }),
    update: (id: number, body: Schema.WeddingUpdate) =>
      request<Schema.WeddingPublic>(`/weddings/${id}`, { method: 'PATCH', body }),
    delete: (id: number) =>
      request<void>(`/weddings/${id}`, { method: 'DELETE' }),
  },

  guests: {
    list: (
      weddingId: number,
      params?: { cursor?: string; limit?: number; rsvp?: Schema.RSVPStatus },
    ) =>
      request<Schema.GuestList>(`/weddings/${weddingId}/guests`, { query: params }),
    get: (weddingId: number, guestId: number) =>
      request<Schema.GuestPublic>(`/weddings/${weddingId}/guests/${guestId}`),
    create: (weddingId: number, body: Schema.GuestCreate) =>
      request<Schema.GuestPublic>(`/weddings/${weddingId}/guests`, { method: 'POST', body }),
    update: (weddingId: number, guestId: number, body: Schema.GuestUpdate) =>
      request<Schema.GuestPublic>(`/weddings/${weddingId}/guests/${guestId}`, {
        method: 'PATCH',
        body,
      }),
    delete: (weddingId: number, guestId: number) =>
      request<void>(`/weddings/${weddingId}/guests/${guestId}`, { method: 'DELETE' }),
    bulkRsvp: (weddingId: number, body: Schema.BulkRSVPUpdate) =>
      request<Schema.BulkRSVPResult>(`/weddings/${weddingId}/guests/bulk-rsvp`, {
        method: 'POST',
        body,
      }),
    importCsv: (weddingId: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return request<Schema.CSVImportResult>(`/weddings/${weddingId}/guests/import`, {
        method: 'POST',
        formData: fd,
      })
    },
  },

  budget: {
    listCategories: (weddingId: number) =>
      request<Schema.BudgetCategoryPublic[]>(`/weddings/${weddingId}/budget/categories`),
    createCategory: (weddingId: number, body: Schema.BudgetCategoryCreate) =>
      request<Schema.BudgetCategoryPublic>(`/weddings/${weddingId}/budget/categories`, {
        method: 'POST',
        body,
      }),
    updateCategory: (weddingId: number, catId: number, body: Schema.BudgetCategoryUpdate) =>
      request<Schema.BudgetCategoryPublic>(
        `/weddings/${weddingId}/budget/categories/${catId}`,
        { method: 'PATCH', body },
      ),
    deleteCategory: (weddingId: number, catId: number) =>
      request<void>(`/weddings/${weddingId}/budget/categories/${catId}`, { method: 'DELETE' }),
    scale: (weddingId: number, body: Schema.ScaleBudgetRequest) =>
      request<Schema.ScaleBudgetResult>(`/weddings/${weddingId}/budget/scale`, {
        method: 'POST',
        body,
      }),
    listExpenses: (weddingId: number) =>
      request<Schema.ExpensePublic[]>(`/weddings/${weddingId}/budget/expenses`),
    createExpense: (weddingId: number, body: Schema.ExpenseCreate) =>
      request<Schema.ExpensePublic>(`/weddings/${weddingId}/budget/expenses`, {
        method: 'POST',
        body,
      }),
    updateExpense: (weddingId: number, expId: number, body: Schema.ExpenseUpdate) =>
      request<Schema.ExpensePublic>(`/weddings/${weddingId}/budget/expenses/${expId}`, {
        method: 'PATCH',
        body,
      }),
    deleteExpense: (weddingId: number, expId: number) =>
      request<void>(`/weddings/${weddingId}/budget/expenses/${expId}`, { method: 'DELETE' }),
    summary: (weddingId: number) =>
      request<Schema.BudgetSummary>(`/weddings/${weddingId}/budget/summary`),
  },

  vendors: {
    list: (weddingId: number, status?: Schema.VendorStatus) =>
      request<Schema.VendorPublic[]>(`/weddings/${weddingId}/vendors`, {
        query: status ? { status } : undefined,
      }),
    get: (weddingId: number, vendorId: number) =>
      request<Schema.VendorPublic>(`/weddings/${weddingId}/vendors/${vendorId}`),
    create: (weddingId: number, body: Schema.VendorCreate) =>
      request<Schema.VendorPublic>(`/weddings/${weddingId}/vendors`, { method: 'POST', body }),
    update: (weddingId: number, vendorId: number, body: Schema.VendorUpdate) =>
      request<Schema.VendorPublic>(`/weddings/${weddingId}/vendors/${vendorId}`, {
        method: 'PATCH',
        body,
      }),
    delete: (weddingId: number, vendorId: number) =>
      request<void>(`/weddings/${weddingId}/vendors/${vendorId}`, { method: 'DELETE' }),
  },

  checklist: {
    list: (
      weddingId: number,
      params?: {
        category?: Schema.ChecklistCategory
        priority?: Schema.ChecklistPriority
        completed?: boolean
      },
    ) =>
      request<Schema.ChecklistItemPublic[]>(`/weddings/${weddingId}/checklist`, {
        query: params,
      }),
    create: (weddingId: number, body: Schema.ChecklistItemCreate) =>
      request<Schema.ChecklistItemPublic>(`/weddings/${weddingId}/checklist`, {
        method: 'POST',
        body,
      }),
    update: (weddingId: number, itemId: number, body: Schema.ChecklistItemUpdate) =>
      request<Schema.ChecklistItemPublic>(`/weddings/${weddingId}/checklist/${itemId}`, {
        method: 'PATCH',
        body,
      }),
    delete: (weddingId: number, itemId: number) =>
      request<void>(`/weddings/${weddingId}/checklist/${itemId}`, { method: 'DELETE' }),
    bulkComplete: (weddingId: number, body: Schema.BulkCompleteRequest) =>
      request<Schema.BulkCompleteResult>(`/weddings/${weddingId}/checklist/bulk-complete`, {
        method: 'POST',
        body,
      }),
  },

  tables: {
    list: (weddingId: number) =>
      request<Schema.WeddingTablePublic[]>(`/weddings/${weddingId}/tables`),
    listWithGuests: (weddingId: number) =>
      request<Schema.WeddingTableWithGuests[]>(`/weddings/${weddingId}/tables/with-guests`),
    create: (weddingId: number, body: Schema.WeddingTableCreate) =>
      request<Schema.WeddingTablePublic>(`/weddings/${weddingId}/tables`, {
        method: 'POST',
        body,
      }),
    update: (weddingId: number, tableId: number, body: Schema.WeddingTableUpdate) =>
      request<Schema.WeddingTablePublic>(`/weddings/${weddingId}/tables/${tableId}`, {
        method: 'PATCH',
        body,
      }),
    delete: (weddingId: number, tableId: number) =>
      request<void>(`/weddings/${weddingId}/tables/${tableId}`, { method: 'DELETE' }),
  },
}
