import { api } from '@/lib/api'
import { useI18n } from '@/i18n'

const providers = [
  { id: 'line', label: 'LINE', color: 'bg-[#06C755] text-white' },
  { id: 'google', label: 'Google', color: 'bg-white border border-gray-300 text-gray-700' },
  { id: 'facebook', label: 'Facebook', color: 'bg-[#1877F2] text-white' },
]

export function SocialButtons() {
  const { t } = useI18n()

  const start = async (provider: string) => {
    try {
      const resp = await api.get(`/auth/oauth/${provider}/start`)
      window.location.href = resp.data.authorization_url
    } catch {
      alert(`${provider} login is not configured yet`)
    }
  }

  return (
    <div>
      <div className="my-4 flex items-center gap-3 text-xs text-gray-400">
        <span className="h-px flex-1 bg-gray-200" />
        {t('or_continue_with')}
        <span className="h-px flex-1 bg-gray-200" />
      </div>
      <div className="grid gap-2">
        {providers.map((p) => (
          <button key={p.id} onClick={() => start(p.id)} className={`btn ${p.color}`}>
            {p.label}
          </button>
        ))}
      </div>
    </div>
  )
}
