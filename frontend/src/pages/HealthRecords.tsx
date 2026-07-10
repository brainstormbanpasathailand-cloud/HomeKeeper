import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { HealthRecord } from '@/lib/types'

interface Summary {
  total_spent: number
  records: number
  by_year: Record<string, number>
}

export default function HealthRecords() {
  const { t } = useI18n()
  const { data: records } = useQuery({
    queryKey: ['health-records'],
    queryFn: async () => (await api.get<HealthRecord[]>('/health-records')).data,
  })
  const { data: summary } = useQuery({
    queryKey: ['health-summary'],
    queryFn: async () => (await api.get<Summary>('/health-records/summary')).data,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t('health_record')}</h1>

      {summary && (
        <div className="grid grid-cols-2 gap-3">
          <div className="card text-center">
            <div className="text-2xl font-bold text-brand-700">฿{summary.total_spent.toLocaleString()}</div>
            <div className="text-xs text-gray-400">ค่าใช้จ่ายสะสม</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-brand-700">{summary.records}</div>
            <div className="text-xs text-gray-400">งานที่บันทึก</div>
          </div>
        </div>
      )}

      <section>
        <h2 className="mb-2 text-sm font-bold text-gray-700">Timeline การดูแล</h2>
        <div className="space-y-2">
          {(records || []).map((r) => (
            <div key={r.id} className="card">
              <div className="flex items-center justify-between">
                <div className="font-medium">{r.issue || 'งานบริการ'}</div>
                <div className="text-xs text-gray-400">{r.service_date}</div>
              </div>
              {r.work_performed && <p className="mt-1 text-xs text-gray-500">{r.work_performed}</p>}
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                {r.total_cost != null && <span className="chip bg-gray-100 text-gray-600">฿{Number(r.total_cost).toLocaleString()}</span>}
                {r.warranty_end && <span className="chip bg-green-100 text-green-700">ประกันถึง {r.warranty_end}</span>}
                {r.next_maintenance_date && <span className="chip bg-amber-100 text-amber-700">ตรวจครั้งหน้า {r.next_maintenance_date}</span>}
              </div>
              {(r.before_photos?.length || r.after_photos?.length) && (
                <div className="mt-2 flex gap-2 overflow-x-auto">
                  {[...(r.before_photos || []), ...(r.after_photos || [])].map((p, i) => (
                    <img key={i} src={p} className="h-16 w-16 rounded-lg object-cover" />
                  ))}
                </div>
              )}
            </div>
          ))}
          {records?.length === 0 && <p className="text-sm text-gray-400">ยังไม่มีประวัติ เมื่อมีงานเสร็จระบบจะบันทึกอัตโนมัติ</p>}
        </div>
      </section>
    </div>
  )
}
