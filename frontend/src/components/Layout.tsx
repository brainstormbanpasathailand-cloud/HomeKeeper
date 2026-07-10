import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { useI18n } from '@/i18n'

const customerNav = [
  { to: '/', key: 'home', icon: '🏠' },
  { to: '/jobs/new', key: 'call_technician', icon: '🔧' },
  { to: '/properties', key: 'my_homes', icon: '🏘️' },
  { to: '/jobs', key: 'my_jobs', icon: '📋' },
  { to: '/account', key: 'account', icon: '👤' },
]

const technicianNav = [
  { to: '/tech', key: 'new_jobs', icon: '🆕' },
  { to: '/jobs', key: 'my_jobs', icon: '📋' },
  { to: '/account', key: 'account', icon: '👤' },
]

const adminNav = [
  { to: '/admin', key: 'dashboard', icon: '📊' },
  { to: '/admin/dispatch', key: 'dispatch', icon: '🗂️' },
  { to: '/admin/technicians', key: 'technician', icon: '🧰' },
  { to: '/account', key: 'account', icon: '👤' },
]

export function Layout() {
  const { user, logout } = useAuth()
  const { t, lang, setLang } = useI18n()
  const navigate = useNavigate()

  const nav =
    user?.role === 'technician'
      ? technicianNav
      : ['admin', 'super_admin', 'dispatcher', 'support'].includes(user?.role || '')
        ? adminNav
        : customerNav

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col bg-gray-50">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-100 bg-white px-4 py-3">
        <button onClick={() => navigate('/')} className="text-lg font-extrabold text-brand-700">
          Home<span className="text-brand-500">Keeper</span>
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setLang(lang === 'th' ? 'en' : 'th')}
            className="chip bg-gray-100 text-gray-600"
          >
            {lang === 'th' ? 'TH' : 'EN'}
          </button>
          <button onClick={() => logout()} className="chip bg-gray-100 text-gray-600">
            {t('logout')}
          </button>
        </div>
      </header>

      <main className="flex-1 px-4 py-4 pb-24">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-10 mx-auto flex max-w-md justify-around border-t border-gray-100 bg-white/95 px-2 py-2 backdrop-blur">
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/' || item.to === '/admin' || item.to === '/tech'}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-0.5 rounded-lg py-1 text-[11px] font-medium ${
                isActive ? 'text-brand-700' : 'text-gray-400'
              }`
            }
          >
            <span className="text-lg">{item.icon}</span>
            {t(item.key)}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
