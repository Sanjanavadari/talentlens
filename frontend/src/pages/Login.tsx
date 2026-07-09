import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'

import { useToast } from '../components/Toast'
import { useAuth } from '../context/AuthContext'
import { getAuthErrorMessage } from '../utils/authErrors'

export function Login() {
  const { login, register, loading, isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    try {
      if (mode === 'login') {
        await login(email.trim(), password)
      } else {
        await register(email.trim(), password)
      }
    } catch (error) {
      showToast(getAuthErrorMessage(error))
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-violet-600">
          TalentLens
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">
          {mode === 'login' ? 'Recruiter sign in' : 'Create recruiter account'}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Access your candidate library and ranking dashboard.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-violet-300"
          >
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <button
          type="button"
          onClick={() => {
            setMode((current) => (current === 'login' ? 'register' : 'login'))
          }}
          className="mt-4 text-sm font-medium text-violet-700 hover:text-violet-900"
        >
          {mode === 'login'
            ? 'Need an account? Register'
            : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  )
}
