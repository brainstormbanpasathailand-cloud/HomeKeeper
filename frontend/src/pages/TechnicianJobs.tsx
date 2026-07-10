import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { Job, Page } from '@/lib/types'
import { StatusBadge } from '@/components/StatusBadge'

export default function TechnicianJobs() {
  const { t } = useI18n()
  const { data } = useQuery({
    queryKey: ['tech-jobs'],
    queryFn: async () => (await api.get<Page<Job>>('/jobs')).data,
  })

  const jobs = data?.items || []
  const pending = jobs.filter((j) => j.status === 'assigned')
  const active = jobs.filter((j) => !['assigned', 'closed', 'cancelled', 'completed'].includes(j.status))

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t('new_jobs')}</h1>
      {pending.length === 0 && <p className="text-sm text-gray-400">ยังไม่มีงานใหม่</p>}
      {pending.map((j) => (
        <Link key={j.id} to={`/jobs/${j.id}`} className="card block border-amber-200 bg-amber-50">
          <div className="flex items-center justify-between">
            <div className="font-medium">{j.title}</div>
            <StatusBadge status={j.status} />
          </div>
          <div className="text-xs text-gray-500">{j.job_number}</div>
        </Link>
      ))}

      <h2 className="pt-2 text-sm font-bold text-gray-700">งานที่กำลังทำ</h2>
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
  )
}
