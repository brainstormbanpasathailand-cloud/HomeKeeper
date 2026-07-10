import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { Job, Page, ServiceCategory } from '@/lib/types'
import { StatusBadge } from '@/components/StatusBadge'

export default function CustomerHome() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => (await api.get<ServiceCategory[]>('/service-categories')).data,
  })
  const { data: jobs } = useQuery({
    queryKey: ['jobs', 'active'],
    queryFn: async () => (await api.get<Page<Job>>('/jobs')).data,
  })

  const active = (jobs?.items || []).filter(
    (j) => !['closed', 'cancelled', 'completed', 'customer_confirmed'].includes(j.status),
  )

  return (
    <div className="space-y-5">
      <button
        onClick={() => navigate('/jobs/new?urgency=emergency')}
        className="w-full rounded-2xl bg-gradient-to-r from-brand-600 to-brand-800 p-5 text-left text-white shadow-lg"
      >
        <div className="text-lg font-bold">🚨 {t('call_urgent')}</div>
        <div className="text-sm text-brand-100">ช่างพร้อมรับงานด่วนใกล้คุณ</div>
      </button>

      <Link to="/jobs/new" className="input flex items-center text-gray-400">
        🔍 {t('search_service')}…
      </Link>

      <section>
        <h2 className="mb-2 text-sm font-bold text-gray-700">{t('popular_categories')}</h2>
        <div className="grid grid-cols-4 gap-3">
          {(categories || []).slice(0, 12).map((c) => (
            <button
              key={c.id}
              onClick={() => navigate(`/jobs/new?category=${c.id}`)}
              className="flex flex-col items-center gap-1 rounded-xl bg-white p-2 text-center shadow-sm"
            >
              <span className="text-xl">{c.icon || '🛠️'}</span>
              <span className="text-[10px] leading-tight text-gray-600">
                {lang === 'th' ? c.name_th : c.name_en || c.name_th}
              </span>
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-bold text-gray-700">{t('in_progress')}</h2>
          <Link to="/jobs" className="text-xs text-brand-700">
            ดูทั้งหมด
          </Link>
        </div>
        {active.length === 0 ? (
          <p className="text-sm text-gray-400">ยังไม่มีงานที่กำลังดำเนินการ</p>
        ) : (
          <div className="space-y-2">
            {active.map((j) => (
              <Link key={j.id} to={`/jobs/${j.id}`} className="card flex items-center justify-between">
                <div>
                  <div className="font-medium">{j.title}</div>
                  <div className="text-xs text-gray-400">{j.job_number}</div>
                </div>
                <StatusBadge status={j.status} />
              </Link>
            ))}
          </div>
        )}
      </section>

      <div className="grid grid-cols-2 gap-3">
        <Link to="/properties" className="card text-center">
          <div className="text-2xl">🏘️</div>
          <div className="mt-1 text-sm font-semibold">{t('my_homes')}</div>
        </Link>
        <Link to="/health" className="card text-center">
          <div className="text-2xl">📗</div>
          <div className="mt-1 text-sm font-semibold">{t('health_record')}</div>
        </Link>
      </div>
    </div>
  )
}
