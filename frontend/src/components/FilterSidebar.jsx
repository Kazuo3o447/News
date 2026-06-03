import { useEffect, useState } from "react"
import axios from "axios"
import { TOPICS as TOPICS_FALLBACK } from "../utils/topics"

// Deprecated: Topics werden aus /api/topics geladen. Diese Datei nur als Fallback.

const PLATFORM_ITEMS = [
  { key: "all",     label: "Alle Plattformen" },
  { key: "windows", label: "Windows / Microsoft" },
  { key: "apple",   label: "Apple / macOS / iOS" },
  { key: "android", label: "Android / Mobile-MDM" },
]

const CATEGORIES = [
  { key: null,        label: "Alle" },
  { key: "KRITISCH",  label: "Kritisch" },
  { key: "NORMAL",    label: "Normal" },
  { key: "DUMP",      label: "Aussortiert" },
  { key: "OFF_TOPIC", label: "Off-Topic" },
]

export default function FilterSidebar({
  search, onSearchChange,
  category, onCategoryChange,
  topic, onTopicChange,
  source, onSourceChange,
  counts,
  hasActiveFilters,
  onReset,
  prefs,
  onToggleTopic,
  onToggleSource,
  onSetShowOffTopic,
  onSetShowDump,
  // new F6
  selectedPlatform,
  onSetSelectedPlatform,
}) {
  const [apiTopics, setApiTopics] = useState(null)

  useEffect(() => {
    axios.get("/api/topics")
      .then(res => setApiTopics(res.data?.topics || null))
      .catch(() => setApiTopics(null))
  }, [])

  const topics = apiTopics || TOPICS_FALLBACK.map(t => ({ key: t.key, label: t.label }))

  function catColor(key) {
    if (key === "KRITISCH")  return "var(--cat-kritisch)"
    if (key === "NORMAL")    return "var(--cat-normal)"
    if (key === "DUMP")      return "var(--cat-dump)"
    if (key === "OFF_TOPIC") return "#9ca3af"
    return "linear-gradient(135deg, var(--gema-red), var(--gema-red-dark))"
  }

  return (
    <aside className="sidebar">
      {/* Suche */}
      <div className="filter-panel">
        <div className="filter-panel__title">
          <span>Suche</span>
          {hasActiveFilters && (
            <button className="filter-panel__reset" onClick={onReset}>Zurücksetzen</button>
          )}
        </div>
        <input
          type="search"
          className="search-input"
          placeholder="Titel oder Quelle filtern…"
          value={search}
          onChange={e => onSearchChange(e.target.value)}
        />
      </div>

      {/* Plattform (new F6 — ganz oben nach Suche) */}
      <div className="filter-panel">
        <div className="filter-panel__title">Plattform</div>
        <div className="filter-list">
          {PLATFORM_ITEMS.map(({ key, label }) => {
            const isActive = (selectedPlatform || "all") === key
            return (
              <button
                key={key}
                className={`filter-item ${isActive ? "filter-item--active" : ""}`}
                onClick={() => onSetSelectedPlatform?.(key)}
              >
                <span className="filter-item__label">{label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Meine Themen */}
      <div className="filter-panel">
        <div className="filter-panel__title">Meine Themen</div>
        <div className="filter-panel__hint">
          Welche Themen interessieren dich? Andere werden ausgeblendet.
        </div>
        <div className="filter-list">
          {topics.map(t => {
            const subscribed = prefs.subscribedTopics.includes(t.key)
            return (
              <label key={t.key} className="filter-check">
                <input
                  type="checkbox"
                  checked={subscribed}
                  onChange={() => onToggleTopic(t.key)}
                />
                <span>{t.label}</span>
                <span className="filter-item__count">{counts.topic?.[t.key] ?? 0}</span>
              </label>
            )
          })}
        </div>
        <label className="filter-check filter-check--toggle">
          <input
            type="checkbox"
            checked={prefs.showOffTopic}
            onChange={e => onSetShowOffTopic(e.target.checked)}
          />
          <span>Off-Topic anzeigen</span>
        </label>
        <label className="filter-check filter-check--toggle">
          <input
            type="checkbox"
            checked={prefs.showDump}
            onChange={e => onSetShowDump(e.target.checked)}
          />
          <span>Aussortiert anzeigen</span>
        </label>
      </div>

      {/* Kritikalität */}
      <div className="filter-panel">
        <div className="filter-panel__title">Kritikalität</div>
        <div className="filter-list">
          {CATEGORIES.map(({ key, label }) => {
            const isActive = category === key
            const count = key === null
              ? counts.category?.all
              : counts.category?.[key]
            const catLabel = key === "DUMP" ? "Aussortiert" : label
            return (
              <button
                key={String(key)}
                className={`filter-item ${isActive ? "filter-item--active" : ""}`}
                onClick={() => onCategoryChange(key)}
              >
                <span className="filter-item__label">
                  <span className="filter-item__dot" style={{ background: catColor(key) }} />
                  {catLabel}
                </span>
                {count != null && <span className="filter-item__count">{count}</span>}
              </button>
            )
          })}
        </div>
      </div>

      {/* Themengebiet */}
      <div className="filter-panel">
        <div className="filter-panel__title">Themengebiet (Schnellfilter)</div>
        <div className="filter-list">
          <button
            className={`filter-item ${topic === null ? "filter-item--active" : ""}`}
            onClick={() => onTopicChange(null)}
          >
            <span className="filter-item__label">Alle Themen</span>
            <span className="filter-item__count">{counts.topic?.__all ?? ""}</span>
          </button>
          {topics.map(t => {
            const isActive = topic === t.key
            const count = counts.topic?.[t.key] ?? 0
            if (count === 0 && !isActive) return null
            return (
              <button
                key={t.key}
                className={`filter-item ${isActive ? "filter-item--active" : ""}`}
                onClick={() => onTopicChange(t.key)}
              >
                <span className="filter-item__label">{t.label}</span>
                <span className="filter-item__count">{count}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Quelle */}
      <div className="filter-panel">
        <div className="filter-panel__title">Quelle</div>
        <div className="filter-list" style={{ maxHeight: 240, overflowY: "auto" }}>
          <button
            className={`filter-item ${source === null ? "filter-item--active" : ""}`}
            onClick={() => onSourceChange(null)}
          >
            <span className="filter-item__label">Alle Quellen</span>
            <span className="filter-item__count">{counts.source?.__all ?? ""}</span>
          </button>
          {Object.entries(counts.source || {})
            .filter(([key]) => key !== "__all")
            .sort((a, b) => b[1] - a[1])
            .map(([name, count]) => {
              const isActive = source === name
              const muted    = prefs.mutedSources.includes(name)
              return (
                <div key={name} className="filter-item-row">
                  <button
                    className={`filter-item ${isActive ? "filter-item--active" : ""} ${muted ? "filter-item--muted" : ""}`}
                    onClick={() => onSourceChange(name)}
                  >
                    <span className="filter-item__label">{name}</span>
                    <span className="filter-item__count">{count}</span>
                  </button>
                  <button
                    className="filter-item__mute"
                    onClick={() => onToggleSource(name)}
                    title={muted ? "Quelle wieder anzeigen" : "Quelle ausblenden"}
                  >
                    {muted ? "🔇" : "·"}
                  </button>
                </div>
              )
            })}
        </div>
      </div>
    </aside>
  )
}
