import { useEffect, useState } from "react"
import Header    from "./components/Header"
import Dashboard from "./pages/Dashboard"
import Settings  from "./pages/Settings"

function prefersDark() {
  try { return window.matchMedia("(prefers-color-scheme: dark)").matches } catch { return false }
}

function loadDarkPref() {
  try {
    const raw = localStorage.getItem("itnews.ui.v4")
    if (!raw) return null
    const p = JSON.parse(raw)
    return typeof p.darkMode === "boolean" ? p.darkMode : null
  } catch { return null }
}

export default function App() {
  const [page,      setPage]      = useState("dashboard")
  const [darkMode,  setDarkMode]  = useState(() => {
    const saved = loadDarkPref()
    return saved !== null ? saved : prefersDark()
  })
  const [kritischUnread, setKritischUnread] = useState(0)

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light")
    try {
      const raw  = localStorage.getItem("itnews.ui.v4")
      const prefs = raw ? JSON.parse(raw) : {}
      localStorage.setItem("itnews.ui.v4", JSON.stringify({ ...prefs, darkMode }))
    } catch {}
  }, [darkMode])

  return (
    <div className="app">
      <Header
        activePage={page}
        onNavigate={setPage}
        kritischUnread={kritischUnread}
        darkMode={darkMode}
        onToggleDark={() => setDarkMode(v => !v)}
      />
      <main className="main">
        {page === "dashboard" && (
          <Dashboard onKritischCount={setKritischUnread} />
        )}
        {page === "settings" && <Settings />}
      </main>
    </div>
  )
}
