import './invitation.css'
import type { InvitationProps } from './fontHelpers'
import { fontImportUrl, pickPairing, primaryColor } from './fontHelpers'

function Rule({ color, opacity = 0.25 }: { color: string; opacity?: number }) {
  return <div style={{ height: '1px', background: color, opacity, margin: '0.18in 0' }} />
}

export function InvitationModern({ theme, wedding }: InvitationProps) {
  const pairing = pickPairing(theme.font_suggestions, 'modern')
  const accent = primaryColor(theme)
  const fontUrl = fontImportUrl([pairing.heading, pairing.body])
  const heading = { fontFamily: `'${pairing.heading}', sans-serif` }
  const body = { fontFamily: `'${pairing.body}', sans-serif` }

  return (
    <>
      <style>{`@import url('${fontUrl}');`}</style>
      <div
        className="invitation invitation-modern"
        style={{ '--primary-color': accent, ...body } as React.CSSProperties}
      >
        {/* Tagline */}
        <div style={{
          ...body, fontWeight: 300, fontSize: '6.5pt',
          letterSpacing: '0.18em', color: accent,
          textTransform: 'lowercase', marginBottom: '0.22in',
          textAlign: 'right',
        }}>
          {theme.tagline}
        </div>

        <Rule color={accent} opacity={0.4} />

        {/* Names */}
        <div>
          <div style={{ ...heading, fontWeight: 300, fontSize: '18pt', color: '#1a1a1a', lineHeight: 1.15, letterSpacing: '-0.01em' }}>
            {wedding.partner1_name}
          </div>
          <div style={{ ...body, fontWeight: 300, fontSize: '9pt', color: accent, margin: '0.07in 0', letterSpacing: '0.06em' }}>
            &amp;
          </div>
          <div style={{ ...heading, fontWeight: 300, fontSize: '18pt', color: '#1a1a1a', lineHeight: 1.15, letterSpacing: '-0.01em' }}>
            {wedding.partner2_name}
          </div>
        </div>

        <Rule color={accent} />

        {/* Invitation text */}
        <div style={{
          ...body, fontWeight: 300, fontSize: '8pt', lineHeight: 1.8,
          color: '#4a4a4a', whiteSpace: 'pre-line',
        }}>
          {theme.invitation_text}
        </div>

        <Rule color={accent} opacity={0.15} />

        {/* Date & venue — vertical list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.08in' }}>
          <div style={{ ...body, fontWeight: 400, fontSize: '8pt', color: '#1a1a1a', letterSpacing: '0.02em' }}>
            {wedding.wedding_date}
          </div>
          {theme.ceremony_time && (
            <div style={{ ...body, fontWeight: 300, fontSize: '7.5pt', color: '#6a6a6a' }}>
              {theme.ceremony_time}
            </div>
          )}
          <div style={{ ...heading, fontWeight: 400, fontSize: '7.5pt', color: accent, letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: '0.06in' }}>
            {wedding.venue_name}
          </div>
          <div style={{ ...body, fontWeight: 300, fontSize: '7pt', color: '#8a8a8a', letterSpacing: '0.03em' }}>
            {wedding.location}
          </div>
        </div>

        {/* RSVP */}
        {theme.rsvp_info && (
          <>
            <Rule color={accent} opacity={0.12} />
            <div>
              <div style={{ ...body, fontWeight: 300, fontSize: '6pt', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#9a9a9a', marginBottom: '3px' }}>
                Kindly reply by
              </div>
              <div style={{ ...body, fontWeight: 400, fontSize: '7.5pt', color: '#4a4a4a' }}>
                {theme.rsvp_info}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}
