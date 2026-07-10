import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'
import { SocialButtons } from '@/components/SocialButtons'

export default function Login() {
  const { login } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(email, password)
      navigate('/')
    } catch {
      setError(t('invalid_credentials'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="text-2xl font-extrabold text-brand-700">
        Home<span className="text-brand-500">Keeper</span>
      </h1>
      <p className="mb-6 text-sm text-gray-500">{t('tagline')}</p>

      <form onSubmit={submit} className="card space-y-3">
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
          {t('login')}
        </button>
        <SocialButtons />
      </form>

      <p className="mt-4 text-center text-sm text-gray-500">
        {t('no_account')}{' '}
        <Link to="/register" className="font-semibold text-brand-700">
          {t('register')}
        </Link>
      </p>
    </div>
  )
}
