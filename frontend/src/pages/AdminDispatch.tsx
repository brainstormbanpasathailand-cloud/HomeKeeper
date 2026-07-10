import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Job, Page, User } from '@/lib/types'
import { StatusBadge } from '@/components/StatusBadge'

export default function AdminDispatch() {
  const qc = useQueryClient()

  const { data: jobs } = useQuery({
    queryKey: ['admin-jobs'],
    queryFn: async () => (await api.get<Page<Job>>('/jobs')).data,
  })
  const { data: techs } = useQuery({
    queryKey: ['admin-techs'],
    queryFn: async () => (await api.get<Page<User>>('/admin/users', { params: { role: 'technician' } })).data,
  })

  const assign = useMutation({
    mutationFn: async (v: { jobId: number; technicianId: number }) =>
      api.post(`/admin/jobs/${v.jobId}/assign`, { technician_id: v.technicianId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-jobs'] }),
  })

  const dispatchable = (jobs?.items || []).filter((j) =>
    ['requested', 'searching', 'reviewing', 'rejected'].includes(j.status),
  )

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">มอบหมายงาน</h1>
      {dispatchable.length === 0 && <p className="text-sm text-gray-400">ไม่มีงานที่รอมอบหมาย</p>}
      {dispatchable.map((j) => (
        <div key={j.id} className="card space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">{j.title}</div>
              <div className="text-xs text-gray-400">
                {j.job_number} · {j.urgency}
              </div>
            </div>
            <StatusBadge status={j.status} />
          </div>
          <select
            className="input"
            defaultValue=""
            onChange={(e) => e.target.value && assign.mutate({ jobId: j.id, technicianId: Number(e.target.value) })}
          >
            <option value="">— มอบหมายให้ช่าง —</option>
            {(techs?.items || []).map((tech) => (
              <option key={tech.id} value={tech.id}>
                {tech.display_name || tech.full_name || tech.email}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  )
}
