import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/AuthContext'
import { LANGS, useI18n } from '@/i18n'

export default function Onboarding() {
  const { refreshUser, user } = useAuth()
  const { t, lang, setLang } = useI18n()
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState(user?.display_name || '')
  const [phone, setPhone] = useState('')
  const [province, setProvince] = useState('')
  const [district, setDistrict] = useState('')
  const [accept, setAccept] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!accept) {
      setError(t('accept_terms_required'))
      return
    }
    try {
      await api.post('/auth/onboarding', {
        display_name: displayName,
        phone,
        province,
        district,
        language: lang,
        accept_tos: accept,
        accept_privacy: accept,
      })
      await refreshUser()
      navigate('/')
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('save_failed'))
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="mb-4 text-xl font-bold">{t('onboarding_title')}</h1>
      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label">{t('choose_language')}</label>
          <div className="grid grid-cols-4 gap-2">
            {LANGS.map((l) => (
              <button
                type="button"
                key={l.code}
                onClick={() => setLang(l.code)}
                className={`rounded-xl border py-2 text-sm ${
                  lang === l.code ? 'border-brand-600 bg-brand-100 text-brand-700' : 'border-gray-200 text-gray-500'
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="label">{t('contact_name')}</label>
          <input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
        </div>
        <div>
          <label className="label">{t('phone')}</label>
          <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="08x-xxx-xxxx" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">{t('province')}</label>
            <input className="input" value={province} onChange={(e) => setProvince(e.target.value)} />
          </div>
          <div>
            <label className="label">{t('district')}</label>
            <input className="input" value={district} onChange={(e) => setDistrict(e.target.value)} />
          </div>
        </div>
        <label className="flex items-start gap-2 text-sm text-gray-600">
          <input type="checkbox" checked={accept} onChange={(e) => setAccept(e.target.checked)} className="mt-1" />
          {t('accept_terms')}
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full">{t('submit')}</button>
      </form>
    </div>
  )
}
