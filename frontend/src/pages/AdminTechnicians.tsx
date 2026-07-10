import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface PendingTech {
  id: number
  user_id: number
  legal_name: string | null
  display_name: string | null
  verification_status: string
  average_rating: number
  completed_jobs: number
}

export default function AdminTechnicians() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['pending-techs'],
    queryFn: async () => (await api.get<PendingTech[]>('/technicians/pending')).data,
  })

  const review = useMutation({
    mutationFn: async (v: { id: number; approve: boolean }) =>
      api.post(`/technicians/${v.id}/review`, { approve: v.approve }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pending-techs'] }),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">อนุมัติช่าง</h1>
      <p className="text-sm text-gray-500">ตรวจสอบและอนุมัติผู้สมัครเป็นช่าง</p>

      {isLoading && <p className="text-gray-400">กำลังโหลด…</p>}
      {data?.length === 0 && <p className="text-sm text-gray-400">ไม่มีช่างที่รอตรวจสอบ</p>}

      <div className="space-y-2">
        {(data || []).map((tech) => (
          <div key={tech.id} className="card space-y-2">
            <div>
              <div className="font-medium">{tech.display_name || tech.legal_name || `ผู้ใช้ #${tech.user_id}`}</div>
              <div className="text-xs text-gray-400">
                สถานะ: {tech.verification_status} · งานสำเร็จ {tech.completed_jobs}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                className="btn-primary flex-1 text-sm"
                disabled={review.isPending}
                onClick={() => review.mutate({ id: tech.id, approve: true })}
              >
                อนุมัติ
              </button>
              <button
                className="btn-outline flex-1 text-sm text-red-600"
                disabled={review.isPending}
                onClick={() => review.mutate({ id: tech.id, approve: false })}
              >
                ปฏิเสธ
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
