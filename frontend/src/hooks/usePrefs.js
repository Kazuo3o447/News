/**
 * Persistente User-Praeferenzen via localStorage.
 * Single-User-Personalisierung - keine Server-Komponente noetig.
 */
import { useEffect, useRef, useState } from "react"
import { TOPICS } from "../utils/topics"

const KEY = "itnews.prefs.v2"

const DEFAULTS = {
  subscribedTopics:  ["security", "microsoft"],
  mutedSources:      [],
  showOffTopic:      false,
  showDump:          false,
  selectedPlatform:  "all",   // "all" | "windows" | "apple" | "android"
  readIds:           [],      // persisted as Array, used as Set internally
  lastVisitAt:       null,    // ISO-String - vorletzter Besuch (fuer "neu seit")
}

const VALID_TOPIC_KEYS = new Set(TOPICS.map(t => t.key))
const VALID_PLATFORMS  = new Set(["all", "windows", "apple", "android"])

function sanitizePrefs(rawPrefs) {
  const merged = { ...DEFAULTS, ...(rawPrefs || {}) }
  return {
    ...merged,
    subscribedTopics: (merged.subscribedTopics || []).filter(key => VALID_TOPIC_KEYS.has(key)),
    mutedSources:     merged.mutedSources || [],
    showOffTopic:     Boolean(merged.showOffTopic),
    showDump:         Boolean(merged.showDump),
    selectedPlatform: VALID_PLATFORMS.has(merged.selectedPlatform) ? merged.selectedPlatform : "all",
    readIds:          Array.isArray(merged.readIds) ? merged.readIds : [],
    lastVisitAt:      merged.lastVisitAt || null,
  }
}

function load() {
  try {
    // Migrate from v1 key
    const rawV1 = localStorage.getItem("itnews.prefs.v1")
    const raw   = localStorage.getItem(KEY)
    if (!raw && rawV1) {
      const v1 = JSON.parse(rawV1)
      return sanitizePrefs(v1)
    }
    if (!raw) return { ...DEFAULTS }
    return sanitizePrefs(JSON.parse(raw))
  } catch {
    return { ...DEFAULTS }
  }
}

export function usePrefs() {
  const [prefs, setPrefs] = useState(load)

  // readIds as an in-memory Set for O(1) lookup
  const readSet = useRef(new Set(prefs.readIds))

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(sanitizePrefs(prefs))) } catch {}
  }, [prefs])

  // ---- existing actions ----
  const toggleTopic = (key) => setPrefs(p => ({
    ...p,
    subscribedTopics: p.subscribedTopics.includes(key)
      ? p.subscribedTopics.filter(t => t !== key)
      : [...p.subscribedTopics, key],
  }))

  const toggleSource = (name) => setPrefs(p => ({
    ...p,
    mutedSources: p.mutedSources.includes(name)
      ? p.mutedSources.filter(s => s !== name)
      : [...p.mutedSources, name],
  }))

  const setShowOffTopic = (v) => setPrefs(p => ({ ...p, showOffTopic: v }))
  const setShowDump     = (v) => setPrefs(p => ({ ...p, showDump: v }))
  const resetPrefs      = ()  => setPrefs({ ...DEFAULTS })

  // ---- new F1 actions ----
  const setSelectedPlatform = (plat) => setPrefs(prev => ({
    ...prev,
    selectedPlatform: VALID_PLATFORMS.has(plat) ? plat : "all",
  }))

  const markRead = (id) => {
    if (readSet.current.has(id)) return
    readSet.current.add(id)
    const newIds = Array.from(readSet.current)
    setPrefs(p => ({ ...p, readIds: newIds }))
  }

  const markAllRead = (ids) => {
    for (const id of ids) readSet.current.add(id)
    const newIds = Array.from(readSet.current)
    setPrefs(p => ({ ...p, readIds: newIds }))
  }

  const isRead = (id) => readSet.current.has(id)

  /**
   * Setzt lastVisitAt auf jetzt (aktuellen Besuch speichern).
   * Gibt den ALTEN Wert zurueck - damit das Dashboard "neu seit letztem Besuch"
   * gegen den vorherigen Zeitstempel rechnen kann.
   * Einmal beim Dashboard-Mount aufrufen.
   */
  const touchVisit = () => {
    const prev = prefs.lastVisitAt
    const now  = new Date().toISOString()
    setPrefs(p => ({ ...p, lastVisitAt: now }))
    return prev
  }

  return {
    prefs,
    // existing
    toggleTopic, toggleSource, setShowOffTopic, setShowDump, resetPrefs,
    // new F1
    setSelectedPlatform,
    markRead, markAllRead, isRead,
    touchVisit,
  }
}
