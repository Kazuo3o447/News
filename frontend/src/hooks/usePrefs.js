/**
 * Persistente User-Präferenzen via localStorage.
 * Single-User-Personalisierung — keine Server-Komponente nötig.
 */
import { useEffect, useState } from 'react'
import { TOPICS } from '../utils/topics'

const KEY = 'itnews.prefs.v1'

const DEFAULTS = {
  subscribedTopics: ['security', 'microsoft'],   // Default-Fokus
  mutedSources:    [],
  showOffTopic:    false,                        // OFF_TOPIC standardmäßig aus
  showDump:        false,                        // DUMP standardmäßig aus
}

const VALID_TOPIC_KEYS = new Set(TOPICS.map(t => t.key))

function sanitizePrefs(rawPrefs) {
  const merged = { ...DEFAULTS, ...(rawPrefs || {}) }
  return {
    ...merged,
    subscribedTopics: (merged.subscribedTopics || []).filter(key => VALID_TOPIC_KEYS.has(key)),
    mutedSources: merged.mutedSources || [],
    showOffTopic: Boolean(merged.showOffTopic),
    showDump: Boolean(merged.showDump),
  }
}

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { ...DEFAULTS }
    return sanitizePrefs(JSON.parse(raw))
  } catch {
    return { ...DEFAULTS }
  }
}

export function usePrefs() {
  const [prefs, setPrefs] = useState(load)

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(sanitizePrefs(prefs))) } catch {}
  }, [prefs])

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

  const resetPrefs = () => setPrefs({ ...DEFAULTS })

  return { prefs, toggleTopic, toggleSource, setShowOffTopic, setShowDump, resetPrefs }
}
