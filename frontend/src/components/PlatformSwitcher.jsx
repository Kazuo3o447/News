/**
 * F2 — PlatformSwitcher: segmentierte Steuerung für Plattform-Filter.
 * Auswahl "Windows" zeigt Windows + cross. "Alle" zeigt alles.
 *
 * Props:
 *   value    : "all" | "windows" | "apple" | "android"
 *   onChange : (key: string) => void
 *   counts   : { all: number, windows: number, apple: number, android: number, cross: number }
 */
export default function PlatformSwitcher({ value, onChange, counts = {} }) {
  const SEGMENTS = [
    { key: 'all',     label: 'Alle',     icon: '🌐' },
    { key: 'windows', label: 'Windows',  icon: '🪟' },
    { key: 'apple',   label: 'Apple',    icon: '' },
    { key: 'android', label: 'Android',  icon: '' },
  ]

  function countFor(key) {
    if (key === 'all') return counts.all ?? null
    // segment shows own platform + cross
    const own   = counts[key]    ?? 0
    const cross = counts['cross'] ?? 0
    return key === 'all' ? null : own + cross
  }

  return (
    <div className="platform-switcher" role="group" aria-label="Plattform-Filter">
      {SEGMENTS.map(({ key, label, icon }) => {
        const active = value === key
        const n      = countFor(key)
        return (
          <button
            key={key}
            className={`platform-switcher__seg${active ? ' --active' : ''}`}
            onClick={() => onChange(key)}
            aria-pressed={active}
            title={key === 'all' ? 'Alle Plattformen' : `${label} + plattformübergreifend`}
          >
            <span>{icon}</span>
            <span>{label}</span>
            {n != null && <span className="platform-switcher__count">{n}</span>}
          </button>
        )
      })}
    </div>
  )
}
