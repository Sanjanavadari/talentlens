import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { CandidatesLibrary } from './pages/CandidatesLibrary'
import { Dashboard } from './pages/Dashboard'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/candidates" element={<CandidatesLibrary />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
