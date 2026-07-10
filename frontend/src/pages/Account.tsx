import { Link } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'

export default function Account() {
  const { user } = useAuth()
  const { t } = useI18n()
  return (
    <div className="space-y-4">
      <div className="card flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-100 text-xl">
          {user?.avatar_url ? <img src={user.avatar_url} className="h-12 w-12 rounded-full" /> : '👤'}
        </div>
        <div>
          <div className="font-semibold">{user?.display_name || user?.full_name}</div>
          <div className="text-xs text-gray-400">{user?.email || user?.phone}</div>
          <span className="chip mt-1 bg-brand-100 text-brand-700">{user?.role}</span>
        </div>
      </div>

      <div className="space-y-1">
        <Link to="/security" className="card flex items-center justify-between">
          <span>🔐 {t('security')}</span>
          <span className="text-gray-300">›</span>
        </Link>
        <Link to="/health" className="card flex items-center justify-between">
          <span>📗 {t('health_record')}</span>
          <span className="text-gray-300">›</span>
        </Link>
        {user?.role === 'customer' && (
          <Link to="/tech-apply" className="card flex items-center justify-between opacity-60">
            <span>🧰 สมัครเป็นช่าง (เร็ว ๆ นี้)</span>
            <span className="text-gray-300">›</span>
          </Link>
        )}
      </div>
    </div>
  )
}
