import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface Stats {
  new_jobs: number
  searching_jobs: number
  in_progress_jobs: number
  disputed_jobs: number
  completed_jobs: number
  urgent_jobs: number
  technicians_pending_review: number
  technicians_online: number
  total_users: number
}

const tiles: { key: keyof Stats; label: string; color: string }[] = [
  { key: 'new_jobs', label: 'งานใหม่', color: 'text-blue-600' },
  { key: 'urgent_jobs', label: 'งานด่วน', color: 'text-red-600' },
  { key: 'searching_jobs', label: 'งานรอช่าง', color: 'text-indigo-600' },
  { key: 'in_progress_jobs', label: 'กำลังดำเนินการ', color: 'text-brand-700' },
  { key: 'disputed_jobs', label: 'มีข้อพิพาท', color: 'text-red-600' },
  { key: 'technicians_pending_review', label: 'ช่างรอตรวจ', color: 'text-amber-600' },
  { key: 'technicians_online', label: 'ช่างออนไลน์', color: 'text-green-600' },
  { key: 'total_users', label: 'ผู้ใช้ทั้งหมด', color: 'text-gray-700' },
]

export default function AdminDashboard() {
  const { data } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: async () => (await api.get<Stats>('/admin/dashboard')).data,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">แดชบอร์ดผู้ดูแลระบบ</h1>
      <div className="grid grid-cols-2 gap-3">
        {tiles.map((tile) => (
          <div key={tile.key} className="card text-center">
            <div className={`text-2xl font-bold ${tile.color}`}>{data ? data[tile.key] : '—'}</div>
            <div className="text-xs text-gray-400">{tile.label}</div>
          </div>
        ))}
      </div>
      <Link to="/admin/dispatch" className="btn-primary w-full">
        ไปหน้ามอบหมายงาน
      </Link>
    </div>
  )
}
