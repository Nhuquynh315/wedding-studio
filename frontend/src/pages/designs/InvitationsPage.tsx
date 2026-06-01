import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Skeleton } from '@/components/ui/skeleton'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { api } from '@/lib/api'
import type { DesignPublic, Layout, Tone } from '@/lib/api-schemas'
import { InvitationPreview } from './invitations/InvitationPreview'

const TONES: Tone[] = ['Romantic', 'Formal', 'Playful', 'Poetic', 'Simple']
const LAYOUTS: Layout[] = ['classic', 'modern', 'romantic']

const SCALE = 1.2
const FRAME_W = 5 * 96 * SCALE   // 576px
const FRAME_H = 7 * 96 * SCALE   // 672px

function SectionHead({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs uppercase tracking-wider text-gray-400">{children}</p>
  )
}

export function InvitationsPage() {
  const { active, activeId, isLoading: weddingsLoading } = useActiveWedding()

  const [style, setStyle] = useState('')
  const [tone, setTone] = useState<Tone>('Romantic')
  const [result, setResult] = useState<DesignPublic | null>(null)
  const [layoutOverride, setLayoutOverride] = useState<Layout | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (body: Parameters<typeof api.designs.generate>[1]) =>
      api.designs.generate(activeId!, body),
    onSuccess: (data) => {
      setResult(data)
      setLayoutOverride(data.theme.layout)
      setApiError(null)
    },
    onError: (err: unknown) => {
      const detail = (err as { detail?: string })?.detail ?? 'Something went wrong.'
      setApiError(detail)
    },
  })

  if (weddingsLoading || !active || !activeId) {
    return (
      <div className="p-8">
        <Skeleton className="h-96" />
      </div>
    )
  }

  function handleSubmit() {
    setApiError(null)
    mutation.mutate({
      partner1_name: active!.partner1_name,
      partner2_name: active!.partner2_name,
      wedding_date: active!.wedding_date,
      location: active!.location,
      venue_name: active!.venue_name,
      style: style || active!.style,
      primary_color: active!.primary_color,
      secondary_color: active!.secondary_color,
      tone,
    })
  }

  const handleDownloadPdf = () => {
    const original = document.querySelector('.preview-scale-wrapper .invitation') as HTMLElement | null
    if (!original) return

    const portal = document.createElement('div')
    portal.className = 'print-portal'
    const clone = original.cloneNode(true) as HTMLElement
    clone.style.transform = 'none'
    clone.style.width = '5in'
    clone.style.height = '7in'
    portal.appendChild(clone)
    document.body.appendChild(portal)

    const cleanup = () => {
      portal.remove()
      window.removeEventListener('afterprint', cleanup)
    }
    window.addEventListener('afterprint', cleanup)

    window.print()
  }

  const weddingFields = {
    partner1_name: active.partner1_name,
    partner2_name: active.partner2_name,
    wedding_date: active.wedding_date,
    location: active.location,
    venue_name: active.venue_name,
  }

  const activeLayout: Layout = layoutOverride ?? result?.theme.layout ?? 'classic'

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-2">
        <h1 className="font-serif text-3xl">Invitations</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-8 items-start">
        {/* ── Form ─────────────────────────────────────── */}
        <form onSubmit={(e) => { e.preventDefault(); handleSubmit() }} className="space-y-4 lg:sticky lg:top-4 lg:self-start">
          <div className="rounded-md border border-gray-200 bg-gray-50 p-4 space-y-2">
            <div>
              <p className="text-xs uppercase tracking-wider text-gray-500">For wedding</p>
              <p className="font-medium text-sm text-gray-900 mt-1">
                {active.partner1_name} & {active.partner2_name}
              </p>
              <p className="text-xs text-gray-600">{active.venue_name} · {active.wedding_date}</p>
            </div>
            <Link
              to="/settings"
              className="inline-block text-xs text-rose-600 hover:text-rose-700 underline"
            >
              Edit wedding details →
            </Link>
          </div>

          <div className="rounded-md border border-gray-200 bg-white p-4 space-y-4">
            <SectionHead>Customize</SectionHead>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Style</label>
              <input
                type="text"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                placeholder={active.style || 'e.g. garden bohemian, modern minimalist'}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-300"
              />
              <p className="text-xs text-gray-400 mt-1">Defaults to your wedding style if left blank.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value as Tone)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-300 bg-white"
              >
                {TONES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Layout</label>
              <select
                value={result ? activeLayout : ''}
                onChange={(e) => setLayoutOverride(e.target.value as Layout)}
                disabled={!result}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-300 bg-white disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
              >
                {!result && <option value="">AI will choose</option>}
                {LAYOUTS.map((l) => (
                  <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
                ))}
              </select>
            </div>

            {apiError && (
              <div className="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md">
                {apiError}
              </div>
            )}

            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full py-2.5 px-4 text-sm font-medium text-white bg-rose-500 hover:bg-rose-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
            >
              {mutation.isPending ? 'Generating…' : 'Generate Invitation'}
            </button>

            {result && (
              <button
                type="button"
                onClick={handleDownloadPdf}
                className="w-full py-2 px-4 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-md transition-colors"
              >
                Download PDF
              </button>
            )}
          </div>
        </form>

        {/* ── Preview ──────────────────────────────────── */}
        <div>
          <div style={{
            width: FRAME_W,
            height: FRAME_H,
            overflow: 'hidden',
            border: '1px solid #e5e7eb',
            background: '#fff',
            position: 'relative',
            marginBottom: 16,
          }}>
            {mutation.isPending ? (
              <Skeleton className="w-full h-full" />
            ) : result ? (
              <div className="preview-scale-wrapper" style={{ transform: `scale(${SCALE})`, transformOrigin: 'top left', width: '5in', height: '7in' }}>
                <InvitationPreview
                  theme={result.theme}
                  wedding={weddingFields}
                  layoutOverride={layoutOverride ?? undefined}
                />
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-gray-400 p-8 text-center">
                Generate your first invitation to see it here.
              </div>
            )}
          </div>

          {mutation.isPending && (
            <p className="text-sm text-gray-400 text-center mt-2">Generating… this takes 5–15 seconds</p>
          )}
        </div>
      </div>
    </div>
  )
}
