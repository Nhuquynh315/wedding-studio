import { ProfileSection } from '@/pages/settings/ProfileSection'
import { PasswordSection } from '@/pages/settings/PasswordSection'
import { WeddingListSection } from '@/pages/settings/WeddingListSection'

export function SettingsPage() {
  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="font-serif text-3xl mb-6">Settings</h1>
      <div className="space-y-6">
        <ProfileSection />
        <PasswordSection />
        <WeddingListSection />
      </div>
    </div>
  )
}
