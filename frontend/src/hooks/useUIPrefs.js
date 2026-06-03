/**
 * F4 — useUIPrefs: Persistierte UI-Vorlieben via localStorage.
 * Kein Gelesen-Status mehr (→ useReadState/Server).
 */
import { useEffect, useState } from "react"

const KEY = "itnews.ui.v4"

const VALID_PLATFORMS = new Set(["all", "windows", "apple", "android"])
const VALID_VIEWS     = new Set(["unread", "all"])

const DEFAULTS = {
  platform:    "all",
  view:        "unread",  // F1: Default = Ungelesen
  darkMode:    null,      // null = system preference
  lastVisitAt: null,
}

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { ...DEFAULTS }
    const p = JSON.parse(raw)
    return {
      platform:    VALID_PLATFORMS.has(p.platform)  ? p.platform  : DEFAULTS.platform,
      view:        VALID_VIEWS.has(p.view)           ? p.view      : DEFAULTS.view,
      darkMode:    typeof p.darkMode === "boolean"   ? p.darkMode  : null,
      lastVisitAt: p.lastVisitAt ?? null,
    }
  } catch {
    return { ...DEFAULTS }
  }
}

export function useUIPrefs() {
  const [prefs, setPrefs] = useState(load)

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(prefs)) } catch {}
  }, [prefs])

  const setPlatform = (p) => setPrefs(prev =>
    ({ ...prev, platform: VALID_PLATFORMS.has(p) ? p : "all" })
  )
  const setView     = (v) => setPrefs(prev =>
    ({ ...prev, view: VALID_VIEWS.has(v) ? v : "unread" })
  )
  const setDarkMode = (v) => setPrefs(prev => ({ ...prev, darkMode: v }))

  /**
   * Setzt lastVisitAt auf jetzt.
   * Gibt den vorherigen Wert zurück (für "neu seit letztem Besuch"-Logik).
   */
  const touchVisit = () => {
    const prev = prefs.lastVisitAt
    const now  = new Date().toISOString()
    setPrefs(p => ({ ...p, lastVisitAt: now }))
    return prev
  }

  return { prefs, setPlatform, setView, setDarkMode, touchVisit }
}
