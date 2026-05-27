import type { Layout } from '@/lib/api-schemas'
import type { InvitationProps } from './fontHelpers'
import { InvitationClassic } from './InvitationClassic'
import { InvitationModern } from './InvitationModern'
import { InvitationRomantic } from './InvitationRomantic'

interface Props extends InvitationProps {
  layoutOverride?: Layout
}

export function InvitationPreview({ theme, wedding, layoutOverride }: Props) {
  const layout = layoutOverride ?? theme.layout
  const Component =
    layout === 'modern' ? InvitationModern
    : layout === 'romantic' ? InvitationRomantic
    : InvitationClassic
  return <Component theme={theme} wedding={wedding} />
}
