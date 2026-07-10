import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'
import { SocialButtons } from '@/components/SocialButtons'

export default function Register() {
  const { register } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 8) {
      setError('รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร')
      return
    }
    setBusy(true)
    try {
      await register(email, password, name)
      navigate('/onboarding')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'สมัครไม่สำเร็จ')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="mb-6 text-2xl font-extrabold text-brand-700">{t('register')}</h1>
      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label">{t('full_name')}</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <label className="label">{t('email')}</label>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div>
          <label className="label">{t('password')}</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" disabled={busy}>
          {t('register')}
        </button>
        <SocialButtons />
      </form>
      <p className="mt-4 text-center text-sm text-gray-500">
        <Link to="/login" className="font-semibold text-brand-700">
          {t('login')}
        </Link>
      </p>
    </div>
  )
}
