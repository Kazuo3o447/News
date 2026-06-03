/**
 * Plattform-Metadaten — Single Source of Truth.
 * Kein Emoji: vermeidet Encoding-Probleme auf Windows-Systemen.
 * Labels: "Microsoft" statt "Windows" (spiegelt M365/Azure-Schwerpunkt).
 */
export const PLATFORMS = [
  { key: "all",     label: "Alle",      short: "Alle" },
  { key: "windows", label: "Microsoft", short: "MS"   },
  { key: "apple",   label: "Apple",     short: "Apple"},
  { key: "android", label: "Android",   short: "Droid"},
]

export const PLATFORM_LABEL = Object.fromEntries(PLATFORMS.map(p => [p.key, p.label]))
export const PLATFORM_SHORT = Object.fromEntries(PLATFORMS.map(p => [p.key, p.short]))

/** Gibt das Label für einen Plattform-Key zurück (Fallback: key). */
export function platformLabel(key) {
  return PLATFORM_LABEL[key] ?? key ?? "Cross"
}
