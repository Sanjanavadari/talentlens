import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const LINKS = [
  { to: '/', label: 'Rank candidates' },
  { to: '/candidates', label: 'Candidates library' },
] as const

export function AppNav() {
  const location = useLocation()
  const navigate = useNavigate()
  const { logout, user } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {LINKS.map((link) => {
        const active = location.pathname === link.to
        return (
          <Link
            key={link.to}
            to={link.to}
            className={`rounded-xl px-3 py-2 text-sm font-medium transition ${
              active
                ? 'bg-violet-600 text-white'
                : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
            }`}
          >
            {link.label}
          </Link>
        )
      })}
      {user ? (
        <span className="hidden text-sm text-slate-500 sm:inline">{user.email}</span>
      ) : null}
      <button
        type="button"
        onClick={handleLogout}
        className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        Sign out
      </button>
    </div>
  )
}
