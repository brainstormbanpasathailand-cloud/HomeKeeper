import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { Job, Page } from '@/lib/types'
import { StatusBadge } from '@/components/StatusBadge'

export default function Jobs() {
  const { t } = useI18n()
  const { data } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => (await api.get<Page<Job>>('/jobs')).data,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t('my_jobs')}</h1>
      <div className="space-y-2">
        {(data?.items || []).map((j) => (
          <Link key={j.id} to={`/jobs/${j.id}`} className="card flex items-center justify-between">
            <div>
              <div className="font-medium">{j.title}</div>
              <div className="text-xs text-gray-400">
                {j.job_number} · {j.urgency}
              </div>
            </div>
            <StatusBadge status={j.status} />
          </Link>
        ))}
        {data?.items.length === 0 && <p className="text-sm text-gray-400">ยังไม่มีงาน</p>}
      </div>
    </div>
  )
}
