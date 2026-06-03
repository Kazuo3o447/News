/**
 * F1 — PlatformSwitcher: segmentierte Steuerung (Alle · Microsoft · Apple · Android).
 * "Windows" → "Microsoft" intern key bleibt "windows".
 * Zeigt ungelesene Anzahl als Badge.
 *
 * Props:
 *   value    : "all" | "windows" | "apple" | "android"
 *   onChange : (key: string) => void
 *   counts   : { all: number, windows: number, apple: number, android: number, cross: number }
 */
import { PLATFORMS } from "../utils/platforms"

export default function PlatformSwitcher({ value, onChange, counts = {} }) {
  function countFor(key) {
    if (key === "all") return counts.all ?? null
    return (counts[key] ?? 0) + (counts["cross"] ?? 0)
  }

  return (
    <div className="platform-switcher" role="group" aria-label="Plattform-Filter">
      {PLATFORMS.map(({ key, label }) => {
        const active = value === key
        const n      = countFor(key)
        return (
          <button
            key={key}
            className={`platform-switcher__seg${active ? " --active" : ""}`}
            onClick={() => onChange(key)}
            aria-pressed={active}
            title={key === "all" ? "Alle Plattformen" : `${label} + plattformübergreifend`}
          >
            <span className="platform-switcher__label">{label}</span>
            {n != null && n > 0 && (
              <span className={`platform-switcher__count${active ? " --active" : ""}`}>{n}</span>
            )}
          </button>
        )
      })}
    </div>
  )
}
