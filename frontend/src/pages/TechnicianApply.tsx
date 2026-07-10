import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'
import { FileUploadField } from '@/components/FileUploadField'
import type { ServiceCategory } from '@/lib/types'

interface TechProfile {
  id: number
  legal_name: string | null
  display_name: string | null
  verification_status: string
}

interface CategoryChoice {
  min_call_fee: string
  accepts_emergency: boolean
}

interface CertForm {
  certificate_type: string
  issuer: string
  certificate_number: string
  document_url: string | null
}

export default function TechnicianApply() {
  const { t, lang } = useI18n()
  const { user, refreshUser } = useAuth()
  const navigate = useNavigate()
  const qc = useQueryClient()

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
    national_id_or_passport: '',
    date_of_birth: '',
    phone: user?.phone || '',
    province: '',
    district: '',
    years_of_experience: '',
    service_radius_km: '10',
    bio: '',
  })
  const [docs, setDocs] = useState({
    profile_photo: null as string | null,
    identity_document_front: null as string | null,
    identity_document_back: null as string | null,
    selfie_with_document: null as string | null,
  })
  const [chosen, setChosen] = useState<Record<number, CategoryChoice>>({})
  const [certs, setCerts] = useState<CertForm[]>([])
  const [error, setError] = useState('')

  const apply = useMutation({
    mutationFn: async () =>
      api.post('/technicians/apply', {
        legal_name: form.legal_name,
        display_name: form.display_name || null,
        national_id_or_passport: form.national_id_or_passport || null,
        date_of_birth: form.date_of_birth || null,
        phone: form.phone || null,
        province: form.province || null,
        district: form.district || null,
        years_of_experience: form.years_of_experience ? Number(form.years_of_experience) : null,
        service_radius_km: form.service_radius_km ? Number(form.service_radius_km) : 10,
        bio: form.bio || null,
        ...docs,
        categories: Object.entries(chosen).map(([id, c]) => ({
          service_category_id: Number(id),
          min_call_fee: c.min_call_fee ? Number(c.min_call_fee) : null,
          accepts_emergency: c.accepts_emergency,
          accepts_scheduled: true,
        })),
        certificates: certs
          .filter((c) => c.certificate_type.trim())
          .map((c) => ({
            certificate_type: c.certificate_type,
            issuer: c.issuer || null,
            certificate_number: c.certificate_number || null,
            document_url: c.document_url,
          })),
      }),
    onSuccess: async () => {
      await refreshUser()
      qc.invalidateQueries({ queryKey: ['tech-profile'] })
    },
    onError: (e: any) => setError(e?.response?.data?.detail || t('apply_submit_failed')),
  })

  const toggleCategory = (id: number) =>
    setChosen((prev) => {
      const next = { ...prev }
      if (next[id]) delete next[id]
      else next[id] = { min_call_fee: '', accepts_emergency: false }
      return next
    })

  const catLabel = (c?: ServiceCategory) => (c ? (lang === 'th' ? c.name_th : c.name_en || c.name_th) : '')

  if (isLoading) return <p className="text-gray-400">{t('loading')}</p>

  if (profile) {
    const approved = profile.verification_status === 'approved'
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-bold">{t('apply_technician')}</h1>
        <div className="card space-y-2 text-center">
          <div className="text-3xl">{approved ? '✅' : profile.verification_status === 'rejected' ? '❌' : '⏳'}</div>
          <p className="font-medium">{t(`status_${profile.verification_status}`)}</p>
          <p className="text-xs text-gray-400">
            {t('name_label')}: {profile.display_name || profile.legal_name}
          </p>
        </div>
        {approved && (
          <button className="btn-primary w-full" onClick={() => navigate('/tech')}>
            {t('go_tech_jobs')}
          </button>
        )}
        {!approved && (
          <button className="btn-outline w-full" onClick={() => qc.invalidateQueries({ queryKey: ['tech-profile'] })}>
            {t('refresh_status')}
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t('apply_technician')}</h1>
      <p className="text-sm text-gray-500">{t('apply_desc')}</p>

      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          setError('')
          if (Object.keys(chosen).length === 0) return setError(t('choose_one_category'))
          if (!docs.identity_document_front) return setError(t('attach_id_front'))
          if (!docs.selfie_with_document) return setError(t('attach_selfie'))
          apply.mutate()
        }}
      >
        {/* Personal */}
        <div className="card space-y-3">
          <h2 className="text-sm font-bold text-gray-700">{t('personal_info')}</h2>
          <div>
            <label className="label">{t('legal_name')} *</label>
            <input className="input" value={form.legal_name} onChange={(e) => setForm({ ...form, legal_name: e.target.value })} required />
          </div>
          <div>
            <label className="label">{t('display_name')}</label>
            <input className="input" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label">{t('id_or_passport')}</label>
              <input className="input" value={form.national_id_or_passport} onChange={(e) => setForm({ ...form, national_id_or_passport: e.target.value })} />
            </div>
            <div>
              <label className="label">{t('birthdate')}</label>
              <input className="input" type="date" value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">{t('phone')}</label>
            <input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label">{t('province')}</label>
              <input className="input" value={form.province} onChange={(e) => setForm({ ...form, province: e.target.value })} />
            </div>
            <div>
              <label className="label">{t('district')}</label>
              <input className="input" value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label">{t('experience_years')}</label>
              <input className="input" type="number" min="0" value={form.years_of_experience} onChange={(e) => setForm({ ...form, years_of_experience: e.target.value })} />
            </div>
            <div>
              <label className="label">{t('service_radius')}</label>
              <input className="input" type="number" min="1" value={form.service_radius_km} onChange={(e) => setForm({ ...form, service_radius_km: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">{t('introduce_yourself')}</label>
            <textarea className="input" rows={2} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
          </div>
        </div>

        {/* Documents */}
        <div className="card space-y-3">
          <h2 className="text-sm font-bold text-gray-700">{t('id_documents')}</h2>
          <FileUploadField label={t('profile_photo')} folder="tech/profile" value={docs.profile_photo} onChange={(url) => setDocs({ ...docs, profile_photo: url })} />
          <FileUploadField label={t('id_front')} required folder="tech/id" value={docs.identity_document_front} onChange={(url) => setDocs({ ...docs, identity_document_front: url })} />
          <FileUploadField label={t('id_back')} folder="tech/id" value={docs.identity_document_back} onChange={(url) => setDocs({ ...docs, identity_document_back: url })} />
          <FileUploadField label={t('selfie_with_doc')} required folder="tech/selfie" value={docs.selfie_with_document} onChange={(url) => setDocs({ ...docs, selfie_with_document: url })} />
        </div>

        {/* Categories */}
        <div className="card space-y-3">
          <h2 className="text-sm font-bold text-gray-700">{t('categories_accepted')} *</h2>
          <div className="flex flex-wrap gap-2">
            {(categories || []).map((c) => (
              <button
                type="button"
                key={c.id}
                onClick={() => toggleCategory(c.id)}
                className={`chip border ${chosen[c.id] ? 'border-brand-600 bg-brand-100 text-brand-700' : 'border-gray-200 bg-white text-gray-500'}`}
              >
                {catLabel(c)}
              </button>
            ))}
          </div>
          {Object.keys(chosen).length > 0 && (
            <div className="space-y-2 pt-2">
              {Object.keys(chosen).map((idStr) => {
                const id = Number(idStr)
                const c = (categories || []).find((x) => x.id === id)
                return (
                  <div key={id} className="rounded-xl bg-gray-50 p-2">
                    <div className="mb-1 text-xs font-medium text-gray-600">{catLabel(c)}</div>
                    <div className="flex items-center gap-2">
                      <input
                        className="input flex-1"
                        type="number"
                        min="0"
                        placeholder={t('min_call_fee_ph')}
                        value={chosen[id].min_call_fee}
                        onChange={(e) => setChosen({ ...chosen, [id]: { ...chosen[id], min_call_fee: e.target.value } })}
                      />
                      <label className="flex items-center gap-1 text-xs text-gray-600">
                        <input
                          type="checkbox"
                          checked={chosen[id].accepts_emergency}
                          onChange={(e) => setChosen({ ...chosen, [id]: { ...chosen[id], accepts_emergency: e.target.checked } })}
                        />
                        {t('accepts_urgent_short')}
                      </label>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Certificates */}
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-gray-700">{t('certificates_optional')}</h2>
            <button type="button" className="text-xs font-semibold text-brand-700" onClick={() => setCerts([...certs, { certificate_type: '', issuer: '', certificate_number: '', document_url: null }])}>
              + {t('add')}
            </button>
          </div>
          {certs.map((cert, i) => (
            <div key={i} className="space-y-2 rounded-xl bg-gray-50 p-2">
              <input className="input" placeholder={t('cert_type_ph')} value={cert.certificate_type} onChange={(e) => setCerts(certs.map((c, j) => (j === i ? { ...c, certificate_type: e.target.value } : c)))} />
              <div className="grid grid-cols-2 gap-2">
                <input className="input" placeholder={t('issuer')} value={cert.issuer} onChange={(e) => setCerts(certs.map((c, j) => (j === i ? { ...c, issuer: e.target.value } : c)))} />
                <input className="input" placeholder={t('cert_number')} value={cert.certificate_number} onChange={(e) => setCerts(certs.map((c, j) => (j === i ? { ...c, certificate_number: e.target.value } : c)))} />
              </div>
              <FileUploadField label={t('cert_file')} folder="tech/cert" value={cert.document_url} onChange={(url) => setCerts(certs.map((c, j) => (j === i ? { ...c, document_url: url } : c)))} />
              <button type="button" className="text-xs text-red-600" onClick={() => setCerts(certs.filter((_, j) => j !== i))}>
                {t('remove_cert')}
              </button>
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" disabled={apply.isPending}>
          {apply.isPending ? t('submitting') : t('submit')}
        </button>
      </form>
    </div>
  )
}
