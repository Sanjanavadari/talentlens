import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'
import { CandidatesLibrary } from './pages/CandidatesLibrary'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { setUnauthorizedHandler } from './services/api'

function AppRoutes() {
  const { logout } = useAuth()

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout()
      window.location.assign('/login')
    })
    return () => setUnauthorizedHandler(null)
  }, [logout])

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
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
