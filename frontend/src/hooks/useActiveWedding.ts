import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { WeddingPublic } from '@/lib/api-schemas'

const STORAGE_KEY = 'active_wedding_id'

export function useActiveWedding() {
  const weddingsQuery = useQuery({
    queryKey: queryKeys.weddings.list(),
    queryFn: api.weddings.list,
  })

  const [activeId, setActiveIdState] = useState<number | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? parseInt(stored, 10) : null
  })

  // If no active id (or stale id not in list), default to the first wedding.
  useEffect(() => {
    const list = weddingsQuery.data
    if (!list || list.length === 0) return

    const exists = activeId !== null && list.some((w) => w.id === activeId)
    if (!exists) {
      setActiveIdState(list[0].id)
      localStorage.setItem(STORAGE_KEY, String(list[0].id))
    }
  }, [weddingsQuery.data, activeId])

  const setActiveId = (id: number) => {
    setActiveIdState(id)
    localStorage.setItem(STORAGE_KEY, String(id))
  }

  const active: WeddingPublic | null =
    weddingsQuery.data?.find((w) => w.id === activeId) ?? null

  return {
    weddings: weddingsQuery.data ?? [],
    active,
    activeId,
    setActiveId,
    isLoading: weddingsQuery.isLoading,
    isError: weddingsQuery.isError,
    error: weddingsQuery.error,
    refetch: weddingsQuery.refetch,
  }
}
