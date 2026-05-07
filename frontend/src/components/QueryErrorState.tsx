import { AlertTriangle, RefreshCw } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ApiError, AUTH_EXPIRED_EVENT } from '@/lib/api'
import { tokens } from '@/lib/tokens'

type Props = {
  error: unknown
  onRetry: () => void
  resourceName?: string
}

export function QueryErrorState({ error, onRetry, resourceName = 'this data' }: Props) {
  if (error instanceof ApiError && error.status === 401) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto mb-3" />
          <h2 className="font-serif text-xl mb-1">Session expired</h2>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            Your session has expired. Sign in again to continue.
          </p>
          <Button
            onClick={() => {
              tokens.clear()
              window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
            }}
          >
            Sign in again
          </Button>
        </CardContent>
      </Card>
    )
  }

  let title = `Couldn't load ${resourceName}`
  let detail = 'Something went wrong. Please try again.'

  if (error instanceof ApiError) {
    if (error.status === 403) {
      title = 'Access denied'
      detail = "You don't have permission to view this."
    } else if (error.status === 404) {
      title = `We couldn't find ${resourceName}`
      detail = 'It may have been deleted.'
    } else if (error.status >= 500) {
      title = 'The server is having trouble'
      detail = 'Try again in a moment, or contact support if it keeps happening.'
    } else {
      detail = error.problem.detail || error.problem.title || detail
    }
  } else if (error instanceof Error) {
    title = 'Network problem'
    detail = 'Check your connection and try again.'
  }

  return (
    <Card>
      <CardContent className="p-8 text-center">
        <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto mb-3" />
        <h2 className="font-serif text-xl mb-1">{title}</h2>
        <p className="text-sm text-[var(--color-text-muted)] mb-4">{detail}</p>
        <Button onClick={onRetry} variant="outline">
          <RefreshCw className="h-4 w-4 mr-1" />
          Try again
        </Button>
      </CardContent>
    </Card>
  )
}
