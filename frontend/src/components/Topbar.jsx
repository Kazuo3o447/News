/**
 * F1 — Topbar: schlanke Filterleiste über der Artikelliste.
 * Drei Controls: PlatformSwitcher · Suchfeld · Ansicht-Umschalter.
 * Aktive Kontextfilter (topic / source) als entfernbare Chips.
 */
import { useRef, useEffect } from "react"
import PlatformSwitcher from "./PlatformSwitcher"

export default function Topbar({
  platform,
  onPlatformChange,
  platformCounts,
  search,
  onSearchChange,
  view,
  onViewChange,
  topic,
  onTopicClear,
  source,
  onSourceClear,
  searchRef: externalSearchRef,
}) {
  const internalRef = useRef(null)
  const searchRef   = externalSearchRef ?? internalRef

  // Debounce: fire onSearchChange 250 ms after last keystroke
  const debounceRef = useRef(null)
  function handleInput(e) {
    const val = e.target.value
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => onSearchChange(val), 250)
  }

  // Keep input value in sync when cleared externally
  useEffect(() => {
    if (searchRef.current && search === "" && searchRef.current.value !== "") {
      searchRef.current.value = ""
    }
  }, [search, searchRef])

  const hasChips = topic || source

  return (
    <div className="topbar">
      <div className="topbar__row">
        <PlatformSwitcher
          value={platform}
          onChange={onPlatformChange}
          counts={platformCounts}
        />

        <div className="topbar__search-wrap">
          <span className="topbar__search-icon" aria-hidden>&#x2315;</span>
          <input
            ref={searchRef}
            className="topbar__search"
            type="search"
            placeholder="Suchen…"
            defaultValue={search}
            onInput={handleInput}
            aria-label="Artikel suchen"
          />
        </div>

        <div className="topbar__view" role="group" aria-label="Ansicht">
          {[
            { key: "unread", label: "Ungelesen" },
            { key: "all",    label: "Alle" },
          ].map(({ key, label }) => (
            <button
              key={key}
              className={`topbar__view-btn${view === key ? " --active" : ""}`}
              onClick={() => onViewChange(key)}
              aria-pressed={view === key}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {hasChips && (
        <div className="topbar__chips">
          {source && (
            <button className="filter-chip" onClick={onSourceClear}>
              {source} <span aria-hidden>×</span>
            </button>
          )}
          {topic && (
            <button className="filter-chip" onClick={onTopicClear}>
              {topic} <span aria-hidden>×</span>
            </button>
          )}
        </div>
      )}
    </div>
  )
}
