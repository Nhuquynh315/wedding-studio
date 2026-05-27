import './invitation.css'
import type { InvitationProps } from './fontHelpers'
import { fontImportUrl, pickPairing, primaryColor, secondaryColor } from './fontHelpers'

function ThinRule() {
  return <div style={{ width: '1.6in', height: '0.5pt', background: 'var(--primary-color)', opacity: 0.3, margin: '0.12in auto' }} />
}

function Spacer({ size }: { size: 'sm' | 'md' }) {
  return <div style={{ height: size === 'sm' ? '0.12in' : '0.18in' }} />
}

export function InvitationRomantic({ theme, wedding }: InvitationProps) {
  const pairing = pickPairing(theme.font_suggestions, 'romantic')
  const accent = primaryColor(theme)
  const secondary = secondaryColor(theme)
  const fontUrl = fontImportUrl([pairing.heading, pairing.body])
  const script = { fontFamily: `'${pairing.heading}', cursive` }
  const body = { fontFamily: `'${pairing.body}', serif` }

  return (
    <>
      <style>{`@import url('${fontUrl}');`}</style>
      <div
        className="invitation invitation-romantic"
        style={{ '--primary-color': accent } as React.CSSProperties}
      >
        {/* Secondary-color background wash */}
        <div style={{
          position: 'absolute', inset: 0,
          background: secondary, opacity: 0.05,
          pointerEvents: 'none',
        }} />

        {/* Top floral ornament */}
        <div style={{ fontSize: '16pt', color: accent, textAlign: 'center', lineHeight: 1 }}>❀</div>
        <Spacer size="sm" />

        {/* Tagline — italic, mixed-case */}
        <div style={{
          ...body, fontStyle: 'italic', fontWeight: 300, fontSize: '8pt',
          color: accent, textAlign: 'center', letterSpacing: '0.03em',
          margin: '0 auto', maxWidth: '3.2in',
        }}>
          {theme.tagline}
        </div>

        <ThinRule />

        {/* Names in script */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ ...body, fontWeight: 300, fontSize: '6.5pt', letterSpacing: '0.09em', textTransform: 'uppercase', color: '#9a8a80', marginBottom: '0.1in' }}>
            Together with their families
          </div>
          <div style={{ ...script, fontSize: '28pt', color: '#2c2420', lineHeight: 1.2 }}>
            {wedding.partner1_name}
          </div>
          <div style={{ ...body, fontStyle: 'italic', fontWeight: 300, fontSize: '10pt', color: accent, margin: '0.04in 0', lineHeight: 1 }}>
            ✿ &amp; ✿
          </div>
          <div style={{ ...script, fontSize: '28pt', color: '#2c2420', lineHeight: 1.2 }}>
            {wedding.partner2_name}
          </div>
        </div>

        <ThinRule />

        {/* Invitation text */}
        <div style={{
          ...body, fontWeight: 300, fontSize: '8.5pt', lineHeight: 1.75,
          textAlign: 'center', color: '#4a3e38',
          maxWidth: '3.2in', overflow: 'hidden',
          margin: '0 auto', whiteSpace: 'pre-line',
        }}>
          {theme.invitation_text}
        </div>

        <ThinRule />

        {/* Date & venue */}
        <div style={{ textAlign: 'center' }}>
          <p style={{ ...body, fontStyle: 'italic', fontWeight: 300, fontSize: '8.5pt', color: '#2c2420', lineHeight: 1.6, marginBottom: '0.08in' }}>
            {wedding.wedding_date}
            {theme.ceremony_time && <><br />{theme.ceremony_time}</>}
          </p>
          <p style={{ ...body, fontWeight: 400, fontSize: '7.5pt', letterSpacing: '0.09em', textTransform: 'uppercase', color: accent, marginBottom: '3px' }}>
            {wedding.venue_name}
          </p>
          <p style={{ ...body, fontWeight: 300, fontSize: '7pt', color: '#7a6a60', letterSpacing: '0.04em' }}>
            {wedding.location}
          </p>
        </div>

        {/* RSVP */}
        {theme.rsvp_info && (
          <>
            <div style={{ width: '1.4in', height: '0.5pt', background: accent, opacity: 0.3, margin: '0.12in auto' }} />
            <div style={{ textAlign: 'center' }}>
              <p style={{ ...body, fontWeight: 400, fontSize: '6pt', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#9a8a80', marginBottom: '3px' }}>
                Kindly Reply By
              </p>
              <p style={{ ...body, fontStyle: 'italic', fontWeight: 300, fontSize: '7.5pt', color: '#4a3e38' }}>
                {theme.rsvp_info}
              </p>
            </div>
          </>
        )}

        <Spacer size="sm" />
        <div style={{ fontSize: '10pt', color: accent, letterSpacing: '0.12in', textAlign: 'center' }}>❀ ✿ ❀</div>
      </div>
    </>
  )
}
