import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { Asset, Property } from '@/lib/types'

export default function PropertyDetail() {
  const { id } = useParams()
  const { t } = useI18n()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: '', brand: '', model: '', serial_number: '', warranty_end: '' })

  const { data: property } = useQuery({
    queryKey: ['property', id],
    queryFn: async () => (await api.get<Property>(`/properties/${id}`)).data,
  })
  const { data: assets } = useQuery({
    queryKey: ['assets', id],
    queryFn: async () => (await api.get<Asset[]>(`/properties/${id}/assets`)).data,
  })

  const create = useMutation({
    mutationFn: async () =>
      api.post(`/properties/${id}/assets`, {
        ...form,
        warranty_end: form.warranty_end || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets', id] })
      setOpen(false)
      setForm({ name: '', brand: '', model: '', serial_number: '', warranty_end: '' })
    },
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold">{property?.name}</h1>
        <p className="text-xs text-gray-400">{property ? t(`ptype_${property.property_type}`) : ''}</p>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-gray-700">{t('assets_in_property')}</h2>
        <button className="btn-primary" onClick={() => setOpen(true)}>
          + {t('add_asset')}
        </button>
      </div>

      {open && (
        <div className="card space-y-2">
          <input className="input" placeholder={t('asset_name_ph')} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <input className="input" placeholder={t('brand')} value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
            <input className="input" placeholder={t('model')} value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
          </div>
          <input className="input" placeholder={t('serial_number')} value={form.serial_number} onChange={(e) => setForm({ ...form, serial_number: e.target.value })} />
          <div>
            <label className="label">{t('warranty_end')}</label>
            <input className="input" type="date" value={form.warranty_end} onChange={(e) => setForm({ ...form, warranty_end: e.target.value })} />
          </div>
          <div className="flex gap-2">
            <button className="btn-primary flex-1" disabled={!form.name || create.isPending} onClick={() => create.mutate()}>
              {t('save')}
            </button>
            <button className="btn-outline" onClick={() => setOpen(false)}>
              {t('cancel')}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {(assets || []).map((a) => (
          <div key={a.id} className="card">
            <div className="font-medium">{a.name}</div>
            <div className="text-xs text-gray-400">
              {[a.brand, a.model, a.serial_number].filter(Boolean).join(' · ')}
            </div>
            {a.warranty_end && <div className="mt-1 text-xs text-brand-700">{t('warranty_until')} {a.warranty_end}</div>}
          </div>
        ))}
        {assets?.length === 0 && <p className="text-sm text-gray-400">{t('no_assets')}</p>}
      </div>
    </div>
  )
}
