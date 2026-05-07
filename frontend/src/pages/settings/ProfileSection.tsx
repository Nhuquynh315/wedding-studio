import { Card, CardContent } from '@/components/ui/card'

export function ProfileSection() {
  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="font-serif text-xl mb-1">Profile</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Profile editing is not yet available. Contact support to update your name or email.
        </p>
      </CardContent>
    </Card>
  )
}
