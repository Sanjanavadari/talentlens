import { useEffect } from 'react'
import { BrowserRouter, Route, Routes, useNavigate } from 'react-router-dom'

import { ProtectedRoute } from './components/ProtectedRoute'
import { ToastProvider } from './components/Toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import { CandidatesLibrary } from './pages/CandidatesLibrary'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { setUnauthorizedHandler } from './services/api'

function AppRoutes() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout()
      navigate('/login', { replace: true })
    })
    return () => setUnauthorizedHandler(null)
  }, [logout, navigate])

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/candidates" element={<CandidatesLibrary />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
