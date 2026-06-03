import { useState } from 'react'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

export default function App() {
  const [page, setPage] = useState('dashboard')

  return (
    <div className="app">
      <Header activePage={page} onNavigate={setPage} />
      <main className="main">
        {page === 'dashboard' && <Dashboard />}
        {page === 'settings'  && <Settings />}
      </main>
    </div>
  )
}
