import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/AuthContext'

export default function OAuthCallback() {
  const { provider } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { setSession } = useAuth()
  const [error, setError] = useState('')
  const ran = useRef(false)

  useEffect(() => {
    if (ran.current) return
    ran.current = true
    const code = params.get('code')
    const state = params.get('state')
    if (!code || !state) {
      setError('ข้อมูล callback ไม่ครบถ้วน')
      return
    }
    api
      .post(`/auth/oauth/${provider}/callback`, { code, state })
      .then(async (resp) => {
        await setSession(resp.data.access_token, resp.data.refresh_token)
        navigate('/')
      })
      .catch((err) => setError(err?.response?.data?.detail || 'เข้าสู่ระบบไม่สำเร็จ'))
  }, [provider, params, navigate, setSession])

  return (
    <div className="flex h-screen items-center justify-center px-6 text-center">
      {error ? (
        <div>
          <p className="text-red-600">{error}</p>
          <button className="btn-outline mt-4" onClick={() => navigate('/login')}>
            กลับไปเข้าสู่ระบบ
          </button>
        </div>
      ) : (
        <p className="text-gray-400">กำลังเข้าสู่ระบบ…</p>
      )}
    </div>
  )
}
