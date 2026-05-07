export const queryKeys = {
  auth: {
    me: () => ['auth', 'me'] as const,
  },
  weddings: {
    all: () => ['weddings'] as const,
    list: () => ['weddings', 'list'] as const,
    detail: (id: number) => ['weddings', 'detail', id] as const,
  },
  guests: {
    all: (weddingId: number) => ['guests', weddingId] as const,
    list: (weddingId: number, params?: Record<string, unknown>) =>
      params
        ? (['guests', weddingId, 'list', params] as const)
        : (['guests', weddingId, 'list'] as const),
    detail: (weddingId: number, guestId: number) =>
      ['guests', weddingId, 'detail', guestId] as const,
  },
  budget: {
    all: (weddingId: number) => ['budget', weddingId] as const,
    categories: (weddingId: number) => ['budget', weddingId, 'categories'] as const,
    expenses: (weddingId: number) => ['budget', weddingId, 'expenses'] as const,
    summary: (weddingId: number) => ['budget', weddingId, 'summary'] as const,
  },
  vendors: {
    all: (weddingId: number) => ['vendors', weddingId] as const,
    list: (weddingId: number, status?: string) =>
      status
        ? (['vendors', weddingId, 'list', status] as const)
        : (['vendors', weddingId, 'list'] as const),
    detail: (weddingId: number, vendorId: number) =>
      ['vendors', weddingId, 'detail', vendorId] as const,
  },
  checklist: {
    all: (weddingId: number) => ['checklist', weddingId] as const,
    list: (weddingId: number, params?: Record<string, unknown>) =>
      params
        ? (['checklist', weddingId, 'list', params] as const)
        : (['checklist', weddingId, 'list'] as const),
  },
  tables: {
    all: (weddingId: number) => ['tables', weddingId] as const,
    list: (weddingId: number) => ['tables', weddingId, 'list'] as const,
    withGuests: (weddingId: number) => ['tables', weddingId, 'with-guests'] as const,
  },
}
