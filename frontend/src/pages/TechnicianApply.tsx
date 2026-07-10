import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'
import type { ServiceCategory } from '@/lib/types'

interface TechProfile {
  id: number
  legal_name: string | null
  display_name: string | null
  verification_status: string
}

const STATUS_LABEL: Record<string, string> = {
  submitted: 'ส่งใบสมัครแล้ว กำลังรอแอดมินตรวจสอบ',
  under_review: 'แอดมินกำลังตรวจสอบเอกสาร',
  approved: 'ได้รับการอนุมัติแล้ว 🎉 คุณเป็นช่างแล้ว',
  rejected: 'ใบสมัครไม่ผ่านการอนุมัติ กรุณาติดต่อฝ่ายสนับสนุน',
  pending: 'ยังไม่ส่งใบสมัคร',
}

export default function TechnicianApply() {
  const { t, lang } = useI18n()
  const { user, refreshUser } = useAuth()
  const navigate = useNavigate()
  const qc = useQueryClient()

  // Existing profile (if any) — 404 means "not applied yet".
  const { data: profile, isLoading } = useQuery<TechProfile | null>({
    queryKey: ['tech-profile'],
    queryFn: async () => {
      try {
        return (await api.get<TechProfile>('/technicians/me')).data
      } catch {
        return null
      }
    },
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => (await api.get<ServiceCategory[]>('/service-categories')).data,
  })

  const [form, setForm] = useState({
    legal_name: user?.full_name || '',
    display_name: user?.display_name || '',
    phone: user?.phone || '',
    province: '',
    district: '',
    years_of_experience: '',
    service_radius_km: '10',
    bio: '',
  })
  const [categoryIds, setCategoryIds] = useState<number[]>([])
  const [error, setError] = useState('')

  const apply = useMutation({
    mutationFn: async () =>
      api.post('/technicians/apply', {
        legal_name: form.legal_name,
        display_name: form.display_name || null,
        phone: form.phone || null,
        province: form.province || null,
        district: form.district || null,
        years_of_experience: form.years_of_experience ? Number(form.years_of_experience) : null,
        service_radius_km: form.service_radius_km ? Number(form.service_radius_km) : 10,
        bio: form.bio || null,
        category_ids: categoryIds,
      }),
    onSuccess: async () => {
      await refreshUser()
      qc.invalidateQueries({ queryKey: ['tech-profile'] })
    },
    onError: (e: any) => setError(e?.response?.data?.detail || 'ส่งใบสมัครไม่สำเร็จ'),
  })

  const toggleCategory = (id: number) =>
    setCategoryIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  if (isLoading) return <p className="text-gray-400">กำลังโหลด…</p>

  // Already applied → show status instead of the form.
  if (profile) {
    const approved = profile.verification_status === 'approved'
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-bold">สมัครเป็นช่าง</h1>
        <div className="card space-y-2 text-center">
          <div className="text-3xl">{approved ? '✅' : profile.verification_status === 'rejected' ? '❌' : '⏳'}</div>
          <p className="font-medium">{STATUS_LABEL[profile.verification_status] || profile.verification_status}</p>
          <p className="text-xs text-gray-400">ชื่อ: {profile.display_name || profile.legal_name}</p>
        </div>
        {approved && (
          <button className="btn-primary w-full" onClick={() => navigate('/tech')}>
            ไปหน้างานของช่าง
          </button>
        )}
        {!approved && user?.role === 'technician' && (
          <button className="btn-outline w-full" onClick={() => refreshUser()}>
            รีเฟรชสถานะ
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">สมัครเป็นช่าง</h1>
      <p className="text-sm text-gray-500">
        กรอกข้อมูลเพื่อสมัครเป็นช่างผู้ให้บริการ ทีมงานจะตรวจสอบและอนุมัติก่อนคุณจะเริ่มรับงานได้
      </p>

      <form
        className="card space-y-3"
        onSubmit={(e) => {
          e.preventDefault()
          setError('')
          if (categoryIds.length === 0) {
            setError('กรุณาเลือกหมวดงานที่รับอย่างน้อย 1 หมวด')
            return
          }
          apply.mutate()
        }}
      >
        <div>
          <label className="label">ชื่อ-นามสกุลตามบัตร *</label>
          <input className="input" value={form.legal_name} onChange={(e) => setForm({ ...form, legal_name: e.target.value })} required />
        </div>
        <div>
          <label className="label">ชื่อที่แสดง</label>
          <input className="input" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
        </div>
        <div>
          <label className="label">เบอร์โทรศัพท์</label>
          <input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">จังหวัด</label>
            <input className="input" value={form.province} onChange={(e) => setForm({ ...form, province: e.target.value })} />
          </div>
          <div>
            <label className="label">อำเภอ</label>
            <input className="input" value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">ประสบการณ์ (ปี)</label>
            <input className="input" type="number" min="0" value={form.years_of_experience} onChange={(e) => setForm({ ...form, years_of_experience: e.target.value })} />
          </div>
          <div>
            <label className="label">รัศมีบริการ (กม.)</label>
            <input className="input" type="number" min="1" value={form.service_radius_km} onChange={(e) => setForm({ ...form, service_radius_km: e.target.value })} />
          </div>
        </div>
        <div>
          <label className="label">แนะนำตัว</label>
          <textarea className="input" rows={2} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
        </div>

        <div>
          <label className="label">หมวดงานที่รับ *</label>
          <div className="flex flex-wrap gap-2">
            {(categories || []).map((c) => (
              <button
                type="button"
                key={c.id}
                onClick={() => toggleCategory(c.id)}
                className={`chip border ${
                  categoryIds.includes(c.id) ? 'border-brand-600 bg-brand-100 text-brand-700' : 'border-gray-200 bg-white text-gray-500'
                }`}
              >
                {lang === 'th' ? c.name_th : c.name_en || c.name_th}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" disabled={apply.isPending}>
          {t('submit')}
        </button>
      </form>
    </div>
  )
}
