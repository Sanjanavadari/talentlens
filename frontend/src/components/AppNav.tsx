import { Link, useLocation } from 'react-router-dom'

const LINKS = [
  { to: '/', label: 'Rank candidates' },
  { to: '/candidates', label: 'Candidates library' },
] as const

export function AppNav() {
  const location = useLocation()

  return (
    <nav className="flex flex-wrap items-center gap-2">
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
    </nav>
  )
}
