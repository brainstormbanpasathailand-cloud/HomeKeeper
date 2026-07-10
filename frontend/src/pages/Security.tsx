import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'

interface Identity {
  id: number
  provider: string
  provider_email: string | null
}
interface SessionRow {
  id: number
  user_agent: string | null
  ip_address: string | null
  revoked: boolean
}

export default function Security() {
  const { t } = useI18n()
  const { logout } = useAuth()
  const qc = useQueryClient()

  const { data: identities } = useQuery({
    queryKey: ['identities'],
    queryFn: async () => (await api.get<Identity[]>('/auth/identities')).data,
  })
  const { data: sessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => (await api.get<SessionRow[]>('/auth/sessions')).data,
  })

  const unlink = useMutation({
    mutationFn: async (identityId: number) => api.delete(`/auth/identities/${identityId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['identities'] }),
    onError: (e: any) => alert(e?.response?.data?.detail || t('cannot_unlink')),
  })

  const logoutAll = useMutation({
    mutationFn: async () => api.post('/auth/logout-all'),
    onSuccess: () => logout(),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t('security')}</h1>

      <section className="card">
        <h2 className="mb-2 text-sm font-bold text-gray-700">{t('linked_channels')}</h2>
        <div className="space-y-2">
          {(identities || []).map((i) => (
            <div key={i.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <div>
                <div className="text-sm font-medium capitalize">{i.provider}</div>
                {i.provider_email && <div className="text-xs text-gray-400">{i.provider_email}</div>}
              </div>
              <button className="text-xs text-red-600" onClick={() => unlink.mutate(i.id)}>
                {t('unlink')}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h2 className="mb-2 text-sm font-bold text-gray-700">{t('devices_sessions')}</h2>
        <div className="space-y-2">
          {(sessions || []).map((s) => (
            <div key={s.id} className="rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-500">
              {s.user_agent || t('unknown_device')} · {s.ip_address || '-'}
            </div>
          ))}
        </div>
        <button className="btn-outline mt-3 w-full text-red-600" onClick={() => logoutAll.mutate()}>
          {t('logout_all')}
        </button>
      </section>
    </div>
  )
}
