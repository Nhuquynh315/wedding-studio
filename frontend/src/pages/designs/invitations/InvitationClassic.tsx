import './invitation.css'
import type { InvitationProps } from './fontHelpers'
import { fontImportUrl, pickPairing, primaryColor } from './fontHelpers'

function Divider({ color }: { color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.07in', width: '3in', margin: '0 auto' }}>
      <div style={{ flex: 1, height: '0.5pt', background: color, opacity: 0.4 }} />
      <span style={{ fontSize: '5pt', color, lineHeight: 1, opacity: 0.65 }}>◆</span>
      <div style={{ flex: 1, height: '0.5pt', background: color, opacity: 0.4 }} />
    </div>
  )
}

function Spacer({ size }: { size: 'sm' | 'md' }) {
  return <div style={{ height: size === 'sm' ? '0.14in' : '0.18in', lineHeight: 0, fontSize: 0 }} />
}

export function InvitationClassic({ theme, wedding }: InvitationProps) {
  const pairing = pickPairing(theme.font_suggestions, 'classic')
  const accent = primaryColor(theme)
  const fontUrl = fontImportUrl([pairing.heading, pairing.body])
  const heading = { fontFamily: `'${pairing.heading}', serif` }
  const body = { fontFamily: `'${pairing.body}', sans-serif` }

  return (
    <>
      <style>{`@import url('${fontUrl}');`}</style>
      <div
        className="invitation invitation-classic"
        style={{ '--primary-color': accent, ...body, fontWeight: 300 } as React.CSSProperties}
      >
        {/* Top ornament */}
        <div style={{ fontSize: '13pt', color: accent, letterSpacing: '0.12in', textAlign: 'center', lineHeight: 1 }}>
          ✦
        </div>

        {/* Tagline */}
        <div style={{
          ...body, fontWeight: 300, fontSize: '5pt', letterSpacing: '0.12em',
          textTransform: 'uppercase', color: accent, textAlign: 'center',
          margin: '0.09in auto', maxWidth: '3.2in',
          overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis',
        }}>
          {theme.tagline}
        </div>

        <Divider color={accent} />
        <Spacer size="sm" />

        {/* Names */}
        <div style={{ textAlign: 'center' }}>
          <span style={{ ...body, fontWeight: 300, fontSize: '6.5pt', letterSpacing: '0.07em', textTransform: 'uppercase', color: '#9a8a80', display: 'block', marginBottom: '0.1in' }}>
            Together with their families
          </span>
          <span style={{ ...heading, fontSize: '19pt', fontWeight: 300, letterSpacing: '0.03em', color: '#2c2420', lineHeight: 1.25, display: 'block' }}>
            {wedding.partner1_name}
          </span>
          <span style={{ ...heading, fontStyle: 'italic', fontWeight: 300, fontSize: '13pt', color: accent, display: 'block', margin: '0.04in 0', lineHeight: 1 }}>
            &amp;
          </span>
          <span style={{ ...heading, fontSize: '19pt', fontWeight: 300, letterSpacing: '0.03em', color: '#2c2420', lineHeight: 1.25, display: 'block' }}>
            {wedding.partner2_name}
          </span>
        </div>
        <Spacer size="sm" />

        <Divider color={accent} />

        {/* Invitation text */}
        <div style={{
          ...body, fontWeight: 300, fontSize: '8.5pt', lineHeight: 1.75,
          textAlign: 'center', color: '#4a3e38',
          maxWidth: '3.2in', maxHeight: '1in', overflow: 'hidden',
          margin: '0.08in auto 0', whiteSpace: 'pre-line',
        }}>
          {theme.invitation_text}
        </div>
        <Spacer size="md" />

        <Divider color={accent} />
        <Spacer size="sm" />

        {/* Date & venue */}
        <div style={{ textAlign: 'center' }}>
          <p style={{ ...body, fontStyle: 'italic', fontWeight: 300, fontSize: '8.5pt', color: '#2c2420', lineHeight: 1.6, marginBottom: '0.1in' }}>
            {wedding.wedding_date}
            {theme.ceremony_time && <><br />{theme.ceremony_time}</>}
          </p>
          <p style={{ ...body, fontWeight: 400, fontSize: '7.5pt', letterSpacing: '0.09em', textTransform: 'uppercase', color: accent, marginBottom: '4px' }}>
            {wedding.venue_name}
          </p>
          <p style={{ ...body, fontWeight: 300, fontSize: '7pt', color: '#7a6a60', letterSpacing: '0.04em' }}>
            {wedding.location}
          </p>
        </div>

        {/* RSVP */}
        {theme.rsvp_info && (
          <>
            <div style={{ width: '1.6in', height: '0.5pt', background: accent, opacity: 0.3, margin: '0.14in auto' }} />
            <div style={{ textAlign: 'center' }}>
              <p style={{ ...body, fontWeight: 400, fontSize: '6pt', letterSpacing: '0.13em', textTransform: 'uppercase', color: '#9a8a80', marginBottom: '3px' }}>
                Kindly Reply By
              </p>
              <p style={{ ...body, fontWeight: 300, fontSize: '7.5pt', color: '#4a3e38', letterSpacing: '0.02em' }}>
                {theme.rsvp_info}
              </p>
            </div>
          </>
        )}

        <Spacer size="md" />
        <div style={{ fontSize: '8pt', color: accent, letterSpacing: '0.1in', textAlign: 'center' }}>✦ · ✦</div>
      </div>
    </>
  )
}
