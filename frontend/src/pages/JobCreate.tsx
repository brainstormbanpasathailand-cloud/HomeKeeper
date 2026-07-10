import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { Property, ServiceCategory } from '@/lib/types'

const URGENCIES = ['emergency', 'today', 'scheduled', 'quote_first', 'project']

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
      setError(err?.response?.data?.detail || t('create_job_failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t('create_job')}</h1>
      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label">{t('service_type')}</label>
          <select className="input" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
            <option value="">— {t('choose')} —</option>
            {(categories || []).map((c) => (
              <option key={c.id} value={c.id}>
                {lang === 'th' ? c.name_th : c.name_en || c.name_th}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">{t('urgency')}</label>
          <select className="input" value={urgency} onChange={(e) => setUrgency(e.target.value)}>
            {URGENCIES.map((v) => (
              <option key={v} value={v}>
                {t(`urgency_${v}`)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">{t('property_optional')}</label>
          <select className="input" value={propertyId} onChange={(e) => setPropertyId(e.target.value)}>
            <option value="">— {t('not_specified')} —</option>
            {(properties || []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">{t('title')}</label>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder={t('title_ph')} required />
        </div>
        <div>
          <label className="label">{t('problem_detail')}</label>
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
