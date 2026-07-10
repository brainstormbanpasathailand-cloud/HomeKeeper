import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
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
  const { data, isLoading } = useQuery({
    queryKey: ['pending-techs'],
    queryFn: async () => (await api.get<PendingTech[]>('/technicians/pending')).data,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">อนุมัติช่าง</h1>
      <p className="text-sm text-gray-500">แตะเพื่อดูเอกสารและรายละเอียดก่อนอนุมัติ</p>

      {isLoading && <p className="text-gray-400">กำลังโหลด…</p>}
      {data?.length === 0 && <p className="text-sm text-gray-400">ไม่มีช่างที่รอตรวจสอบ</p>}

      <div className="space-y-2">
        {(data || []).map((tech) => (
          <Link key={tech.id} to={`/admin/technicians/${tech.id}`} className="card flex items-center justify-between">
            <div>
              <div className="font-medium">{tech.display_name || tech.legal_name || `ผู้ใช้ #${tech.user_id}`}</div>
              <div className="text-xs text-gray-400">สถานะ: {tech.verification_status}</div>
            </div>
            <span className="chip bg-amber-100 text-amber-700">ตรวจสอบ ›</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
