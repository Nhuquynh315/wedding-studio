import { Card, CardContent } from '@/components/ui/card'

export function PasswordSection() {
  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="font-serif text-xl mb-1">Change password</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Password change is not yet available via the API.
        </p>
      </CardContent>
    </Card>
  )
}
