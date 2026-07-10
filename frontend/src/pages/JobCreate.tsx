import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { Property, ServiceCategory } from '@/lib/types'

const URGENCIES = [
  ['emergency', 'เรียกด่วน'],
  ['today', 'วันนี้'],
  ['scheduled', 'นัดหมายล่วงหน้า'],
  ['quote_first', 'ขอประเมินราคาก่อน'],
  ['project', 'งานโครงการ/ต่อเติม'],
]

export default function JobCreate() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const [params] = useSearchParams()

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => (await api.get<ServiceCategory[]>('/service-categories')).data,
  })
  const { data: properties } = useQuery({
    queryKey: ['properties'],
    queryFn: async () => (await api.get<Property[]>('/properties')).data,
  })

  const [categoryId, setCategoryId] = useState(params.get('category') || '')
  const [propertyId, setPropertyId] = useState('')
  const [urgency, setUrgency] = useState(params.get('urgency') || 'scheduled')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const resp = await api.post(
        '/jobs',
        {
          service_category_id: Number(categoryId),
          property_id: propertyId ? Number(propertyId) : null,
          urgency,
          title,
          problem_description: description,
        },
        { headers: { 'Idempotency-Key': crypto.randomUUID() } },
      )
      navigate(`/jobs/${resp.data.id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'สร้างคำขอไม่สำเร็จ')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t('create_job')}</h1>
      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label">ประเภทบริการ</label>
          <select className="input" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
            <option value="">— เลือก —</option>
            {(categories || []).map((c) => (
              <option key={c.id} value={c.id}>
                {lang === 'th' ? c.name_th : c.name_en || c.name_th}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">ความเร่งด่วน</label>
          <select className="input" value={urgency} onChange={(e) => setUrgency(e.target.value)}>
            {URGENCIES.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">ทรัพย์สิน (ถ้ามี)</label>
          <select className="input" value={propertyId} onChange={(e) => setPropertyId(e.target.value)}>
            <option value="">— ไม่ระบุ —</option>
            {(properties || []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">หัวข้อ</label>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="เช่น แอร์ไม่เย็น" required />
        </div>
        <div>
          <label className="label">รายละเอียดปัญหา</label>
          <textarea className="input" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" disabled={busy}>
          {t('submit')}
        </button>
      </form>
    </div>
  )
}
