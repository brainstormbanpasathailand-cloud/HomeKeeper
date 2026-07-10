import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '@/lib/api'

interface Certificate {
  id: number
  certificate_type: string
  certificate_number: string | null
  issuer: string | null
  document_url: string | null
  verification_status: string
}
interface CategoryRow {
  service_category_id: number
  skill_level: string | null
  min_call_fee: number | null
  accepts_emergency: boolean
}
interface Detail {
  id: number
  legal_name: string | null
  display_name: string | null
  national_id_or_passport: string | null
  phone: string | null
  email: string | null
  province: string | null
  district: string | null
  years_of_experience: number | null
  service_radius_km: number
  bio: string | null
  verification_status: string
  profile_photo: string | null
  identity_document_front: string | null
  identity_document_back: string | null
  selfie_with_document: string | null
  certificates: Certificate[]
  categories: CategoryRow[]
}

function DocImage({ label, url }: { label: string; url: string | null }) {
  if (!url) return null
  return (
    <a href={url} target="_blank" rel="noreferrer" className="block">
      <div className="mb-1 text-xs text-gray-500">{label}</div>
      <img src={url} alt={label} className="h-32 w-full rounded-xl border border-gray-100 object-cover" />
    </a>
  )
}

export default function AdminTechnicianDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['tech-detail', id],
    queryFn: async () => (await api.get<Detail>(`/technicians/${id}`)).data,
  })

  const review = useMutation({
    mutationFn: async (approve: boolean) => api.post(`/technicians/${id}/review`, { approve }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pending-techs'] })
      navigate('/admin/technicians')
    },
  })

  if (isLoading || !data) return <p className="text-gray-400">กำลังโหลด…</p>

  return (
    <div className="space-y-4">
      <button onClick={() => navigate('/admin/technicians')} className="text-sm text-brand-700">
        ‹ กลับ
      </button>
      <h1 className="text-lg font-bold">{data.display_name || data.legal_name}</h1>

      <div className="card space-y-1 text-sm">
        <div><span className="text-gray-400">ชื่อตามบัตร:</span> {data.legal_name}</div>
        <div><span className="text-gray-400">เลขบัตร:</span> {data.national_id_or_passport || '-'}</div>
        <div><span className="text-gray-400">ติดต่อ:</span> {data.phone || '-'} · {data.email || '-'}</div>
        <div><span className="text-gray-400">พื้นที่:</span> {[data.district, data.province].filter(Boolean).join(', ') || '-'} · รัศมี {data.service_radius_km} กม.</div>
        <div><span className="text-gray-400">ประสบการณ์:</span> {data.years_of_experience ?? '-'} ปี</div>
        {data.bio && <div className="text-gray-600">{data.bio}</div>}
      </div>

      <div className="card space-y-3">
        <h2 className="text-sm font-bold text-gray-700">เอกสารยืนยันตัวตน</h2>
        <div className="grid grid-cols-2 gap-3">
          <DocImage label="รูปโปรไฟล์" url={data.profile_photo} />
          <DocImage label="เซลฟี่คู่เอกสาร" url={data.selfie_with_document} />
          <DocImage label="บัตร (หน้า)" url={data.identity_document_front} />
          <DocImage label="บัตร (หลัง)" url={data.identity_document_back} />
        </div>
        {!data.identity_document_front && <p className="text-xs text-amber-600">⚠️ ไม่มีเอกสารยืนยันตัวตน</p>}
      </div>

      <div className="card space-y-2">
        <h2 className="text-sm font-bold text-gray-700">หมวดงานที่รับ</h2>
        {data.categories.map((c) => (
          <div key={c.service_category_id} className="flex items-center justify-between text-sm">
            <span>หมวด #{c.service_category_id} {c.skill_level ? `· ${c.skill_level}` : ''}</span>
            <span className="text-gray-500">
              {c.min_call_fee != null ? `฿${c.min_call_fee}` : '-'} {c.accepts_emergency ? '· รับด่วน' : ''}
            </span>
          </div>
        ))}
        {data.categories.length === 0 && <p className="text-xs text-gray-400">ยังไม่ได้เลือกหมวด</p>}
      </div>

      <div className="card space-y-2">
        <h2 className="text-sm font-bold text-gray-700">ใบรับรอง</h2>
        {data.certificates.map((cert) => (
          <div key={cert.id} className="rounded-xl bg-gray-50 p-2 text-sm">
            <div className="font-medium">{cert.certificate_type}</div>
            <div className="text-xs text-gray-400">
              {[cert.issuer, cert.certificate_number].filter(Boolean).join(' · ') || '-'}
            </div>
            {cert.document_url && (
              <a href={cert.document_url} target="_blank" rel="noreferrer" className="text-xs text-brand-700">
                ดูไฟล์ใบรับรอง →
              </a>
            )}
          </div>
        ))}
        {data.certificates.length === 0 && <p className="text-xs text-gray-400">ไม่มีใบรับรอง</p>}
      </div>

      {['submitted', 'under_review'].includes(data.verification_status) ? (
        <div className="flex gap-2">
          <button className="btn-primary flex-1" disabled={review.isPending} onClick={() => review.mutate(true)}>
            อนุมัติ
          </button>
          <button className="btn-outline flex-1 text-red-600" disabled={review.isPending} onClick={() => review.mutate(false)}>
            ปฏิเสธ
          </button>
        </div>
      ) : (
        <div className="card text-center text-sm text-gray-500">สถานะ: {data.verification_status}</div>
      )}
    </div>
  )
}
