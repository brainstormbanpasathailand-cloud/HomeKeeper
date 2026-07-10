import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useI18n } from '@/i18n'
import type { Property } from '@/lib/types'

const TYPES = ['house', 'condo', 'building', 'shop', 'office', 'car', 'motorcycle']

export default function Properties() {
  const { t } = useI18n()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [type, setType] = useState('house')

  const { data } = useQuery({
    queryKey: ['properties'],
    queryFn: async () => (await api.get<Property[]>('/properties')).data,
  })

  const create = useMutation({
    mutationFn: async () => api.post('/properties', { name, property_type: type }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['properties'] })
      setOpen(false)
      setName('')
    },
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">{t('my_homes')}</h1>
        <button className="btn-primary" onClick={() => setOpen(true)}>
          + {t('add_property')}
        </button>
      </div>

      {open && (
        <div className="card space-y-3">
          <div>
            <label className="label">{t('property_name')}</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label className="label">{t('property_type')}</label>
            <select className="input" value={type} onChange={(e) => setType(e.target.value)}>
              {TYPES.map((v) => (
                <option key={v} value={v}>
                  {t(`ptype_${v}`)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary flex-1" disabled={!name || create.isPending} onClick={() => create.mutate()}>
              {t('save')}
            </button>
            <button className="btn-outline" onClick={() => setOpen(false)}>
              {t('cancel')}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {(data || []).map((p) => (
          <Link key={p.id} to={`/properties/${p.id}`} className="card flex items-center justify-between">
            <div>
              <div className="font-medium">{p.name}</div>
              <div className="text-xs text-gray-400">{t(`ptype_${p.property_type}`)}</div>
            </div>
            <span className="text-gray-300">›</span>
          </Link>
        ))}
        {data?.length === 0 && <p className="text-sm text-gray-400">{t('no_properties')}</p>}
      </div>
    </div>
  )
}
