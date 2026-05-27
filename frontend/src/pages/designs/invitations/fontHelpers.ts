import type { FontPairing, GeneratedTheme, Layout } from '@/lib/api-schemas'

export interface WeddingFields {
  partner1_name: string
  partner2_name: string
  wedding_date: string
  location: string
  venue_name: string
}

export interface InvitationProps {
  theme: GeneratedTheme
  wedding: WeddingFields
}

const SCRIPT_FONTS = ['Tangerine', 'Great Vibes', 'Pinyon Script', 'Alex Brush', 'Parisienne', 'Dancing Script']
const SERIF_FONTS = ['Cormorant Garamond', 'Playfair Display', 'EB Garamond', 'Libre Baskerville', 'Lora', 'Garamond']
const SANS_FONTS = ['Josefin Sans', 'Raleway', 'Montserrat', 'Nunito Sans', 'Poppins', 'Jost', 'Outfit']

export function pickPairing(pairings: FontPairing[], layout: Layout): FontPairing {
  const want =
    layout === 'classic' ? SERIF_FONTS
    : layout === 'modern' ? SANS_FONTS
    : SCRIPT_FONTS
  const match = pairings.find(p =>
    want.some(f => p.heading.toLowerCase().includes(f.toLowerCase()))
  )
  return match ?? pairings[0]
}

export function fontImportUrl(fonts: string[]): string {
  const families = fonts
    .map(f => `family=${f.replace(/ /g, '+')}:ital,wght@0,300;0,400;1,400`)
    .join('&')
  return `https://fonts.googleapis.com/css2?${families}&display=swap`
}

export function primaryColor(theme: GeneratedTheme): string {
  return theme.color_palette.find(c => c.role === 'Primary')?.hex ?? '#b8a9a0'
}

export function secondaryColor(theme: GeneratedTheme): string {
  return theme.color_palette.find(c => c.role === 'Secondary')?.hex ?? '#7a8c5c'
}
