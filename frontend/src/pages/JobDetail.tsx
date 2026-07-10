import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'
import type { Job, Quotation } from '@/lib/types'
import { StatusBadge } from '@/components/StatusBadge'

const TECH_STEPS = ['traveling', 'arrived', 'inspecting', 'in_progress', 'completed']

export default function JobDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const { t } = useI18n()
  const qc = useQueryClient()
  const isTech = user?.role === 'technician'

  const { data: job } = useQuery({
    queryKey: ['job', id],
    queryFn: async () => (await api.get<Job>(`/jobs/${id}`)).data,
  })
  const { data: quotations } = useQuery({
    queryKey: ['quotations', id],
    queryFn: async () => (await api.get<Quotation[]>(`/jobs/${id}/quotations`)).data,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['job', id] })
    qc.invalidateQueries({ queryKey: ['quotations', id] })
  }

  const setStatus = useMutation({
    mutationFn: async (status: string) => api.post(`/jobs/${id}/status`, { status }),
    onSuccess: invalidate,
  })
  const respond = useMutation({
    mutationFn: async (accept: boolean) => api.post(`/jobs/${id}/respond`, { accept }),
    onSuccess: invalidate,
  })
  const decide = useMutation({
    mutationFn: async (v: { quotation_id: number; decision: string }) =>
      api.post(`/quotations/${v.quotation_id}/decision`, { decision: v.decision }),
    onSuccess: invalidate,
  })

  const [labor, setLabor] = useState('')
  const createQuote = useMutation({
    mutationFn: async () => api.post(`/jobs/${id}/quotations`, { labor_cost: Number(labor) || 0 }),
    onSuccess: () => {
      setLabor('')
      invalidate()
    },
  })

  if (!job) return <p className="text-gray-400">กำลังโหลด…</p>

  const latestQuote = quotations?.[quotations.length - 1]

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-lg font-bold">{job.title}</h1>
            <p className="text-xs text-gray-400">
              {job.job_number} · {job.urgency}
            </p>
          </div>
          <StatusBadge status={job.status} />
        </div>
        {job.problem_description && <p className="mt-2 text-sm text-gray-600">{job.problem_description}</p>}
      </div>

      {/* Technician assignment response */}
      {isTech && job.status === 'assigned' && (
        <div className="card space-y-2">
          <p className="text-sm font-medium">คุณได้รับมอบหมายงานนี้</p>
          <div className="flex gap-2">
            <button className="btn-primary flex-1" onClick={() => respond.mutate(true)}>
              รับงาน
            </button>
            <button className="btn-outline flex-1" onClick={() => respond.mutate(false)}>
              ปฏิเสธ
            </button>
          </div>
        </div>
      )}

      {/* Technician workflow steps */}
      {isTech && ['accepted', 'traveling', 'arrived', 'inspecting', 'approved', 'in_progress', 'paused'].includes(job.status) && (
        <div className="card space-y-2">
          <p className="text-sm font-bold text-gray-700">อัปเดตสถานะงาน</p>
          <div className="flex flex-wrap gap-2">
            {TECH_STEPS.map((s) => (
              <button key={s} className="btn-outline text-xs" onClick={() => setStatus.mutate(s)}>
                {s}
              </button>
            ))}
          </div>
          {setStatus.isError && <p className="text-xs text-red-600">ไม่สามารถเปลี่ยนสถานะได้ (ตรวจสอบใบเสนอราคา)</p>}
        </div>
      )}

      {/* Technician quotation form */}
      {isTech && ['inspecting', 'quoted', 'quotation_revision_requested'].includes(job.status) && (
        <div className="card space-y-2">
          <p className="text-sm font-bold text-gray-700">{t('quotation')}</p>
          <input className="input" placeholder="ค่าแรง (บาท)" value={labor} onChange={(e) => setLabor(e.target.value)} />
          <button className="btn-primary w-full" onClick={() => createQuote.mutate()} disabled={createQuote.isPending}>
            ส่งใบเสนอราคา
          </button>
        </div>
      )}

      {/* Quotations list */}
      {(quotations?.length || 0) > 0 && (
        <div className="card space-y-2">
          <p className="text-sm font-bold text-gray-700">{t('quotation')}</p>
          {quotations!.map((q) => (
            <div key={q.id} className="rounded-xl border border-gray-100 p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">เวอร์ชัน {q.version}</span>
                <span className="font-semibold">฿{Number(q.total).toLocaleString()}</span>
              </div>
              <div className="text-xs text-gray-400">สถานะ: {q.status}</div>
              {!isTech && q.status === 'sent' && (
                <div className="mt-2 flex gap-2">
                  <button className="btn-primary flex-1 text-xs" onClick={() => decide.mutate({ quotation_id: q.id, decision: 'approve' })}>
                    {t('approve')}
                  </button>
                  <button className="btn-outline flex-1 text-xs" onClick={() => decide.mutate({ quotation_id: q.id, decision: 'revision' })}>
                    ขอแก้ไข
                  </button>
                  <button className="btn-outline flex-1 text-xs" onClick={() => decide.mutate({ quotation_id: q.id, decision: 'reject' })}>
                    {t('reject')}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Customer review */}
      {!isTech && ['completed', 'customer_confirmed', 'closed'].includes(job.status) && (
        <ReviewForm jobId={job.id} onDone={invalidate} />
      )}

      {latestQuote && !isTech && job.status === 'quoted' && (
        <p className="text-center text-xs text-gray-400">โปรดตรวจสอบและอนุมัติใบเสนอราคาด้านบน</p>
      )}
    </div>
  )
}

function ReviewForm({ jobId, onDone }: { jobId: number; onDone: () => void }) {
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')
  const [done, setDone] = useState(false)
  const submit = useMutation({
    mutationFn: async () => api.post(`/jobs/${jobId}/review`, { rating_quality: rating, comment }),
    onSuccess: () => {
      setDone(true)
      onDone()
    },
  })
  if (done) return <div className="card text-center text-sm text-green-700">ขอบคุณสำหรับรีวิว</div>
  return (
    <div className="card space-y-2">
      <p className="text-sm font-bold text-gray-700">ให้คะแนนงาน</p>
      <div className="flex gap-1 text-2xl">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} onClick={() => setRating(n)}>
            {n <= rating ? '⭐' : '☆'}
          </button>
        ))}
      </div>
      <textarea className="input" rows={2} placeholder="ความคิดเห็น" value={comment} onChange={(e) => setComment(e.target.value)} />
      <button className="btn-primary w-full" onClick={() => submit.mutate()} disabled={submit.isPending}>
        ส่งรีวิว
      </button>
    </div>
  )
}
