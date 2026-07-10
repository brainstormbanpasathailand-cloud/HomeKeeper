import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'

export default function Onboarding() {
  const { refreshUser, user } = useAuth()
  const { t } = useI18n()
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
      setError('กรุณายอมรับเงื่อนไขการใช้งาน')
      return
    }
    try {
      await api.post('/auth/onboarding', {
        display_name: displayName,
        phone,
        province,
        district,
        accept_tos: accept,
        accept_privacy: accept,
      })
      await refreshUser()
      navigate('/')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'บันทึกไม่สำเร็จ')
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="mb-4 text-xl font-bold">{t('onboarding_title')}</h1>
      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label">ชื่อที่ใช้ติดต่อ</label>
          <input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
        </div>
        <div>
          <label className="label">เบอร์โทรศัพท์</label>
          <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="08x-xxx-xxxx" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">จังหวัด</label>
            <input className="input" value={province} onChange={(e) => setProvince(e.target.value)} />
          </div>
          <div>
            <label className="label">อำเภอ</label>
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
