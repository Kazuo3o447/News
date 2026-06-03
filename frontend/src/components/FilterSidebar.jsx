import { TOPICS } from '../utils/topics'

export default function FilterSidebar({
  search, onSearchChange,
  category, onCategoryChange,
  topic, onTopicChange,
  source, onSourceChange,
  counts,
  hasActiveFilters,
  onReset,
  // Personalisierung (localStorage)
  prefs,
  onToggleTopic,
  onToggleSource,
  onSetShowOffTopic,
  onSetShowDump,
}) {
  const CATEGORIES = [
    { key: null,        label: 'Alle',     color: 'linear-gradient(135deg, var(--gema-red), var(--gema-red-dark))' },
    { key: 'KRITISCH',  label: 'Kritisch', color: 'var(--cat-kritisch)' },
    { key: 'NORMAL',    label: 'Normal',   color: 'var(--cat-normal)' },
    { key: 'DUMP',      label: 'Dump',     color: 'var(--cat-dump)' },
    { key: 'OFF_TOPIC', label: 'Off-Topic','color': '#9ca3af' },
  ]

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

      {/* Meine Themen — Personalisierung */}
      <div className="filter-panel">
        <div className="filter-panel__title">Meine Themen</div>
        <div className="filter-panel__hint">
          Welche Themen interessieren dich? Andere werden ausgeblendet.
        </div>
        <div className="filter-list">
          {TOPICS.map(t => {
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
          <span>Dump (Werbung) anzeigen</span>
        </label>
      </div>

      {/* Kritikalität */}
      <div className="filter-panel">
        <div className="filter-panel__title">Kritikalität</div>
        <div className="filter-list">
          {CATEGORIES.map(({ key, label, color }) => {
            const isActive = category === key
            const count = key === null
              ? counts.category?.all
              : counts.category?.[key]
            return (
              <button
                key={String(key)}
                className={`filter-item ${isActive ? 'filter-item--active' : ''}`}
                onClick={() => onCategoryChange(key)}
              >
                <span className="filter-item__label">
                  <span className="filter-item__dot" style={{ background: color }} />
                  {label}
                </span>
                {count != null && <span className="filter-item__count">{count}</span>}
              </button>
            )
          })}
        </div>
      </div>

      {/* Themengebiet — schnellfilter (eines auf einmal) */}
      <div className="filter-panel">
        <div className="filter-panel__title">Themengebiet (Schnellfilter)</div>
        <div className="filter-list">
          <button
            className={`filter-item ${topic === null ? 'filter-item--active' : ''}`}
            onClick={() => onTopicChange(null)}
          >
            <span className="filter-item__label">Alle Themen</span>
            <span className="filter-item__count">{counts.topic?.__all ?? ''}</span>
          </button>
          {TOPICS.map(t => {
            const isActive = topic === t.key
            const count = counts.topic?.[t.key] ?? 0
            if (count === 0 && !isActive) return null
            return (
              <button
                key={t.key}
                className={`filter-item ${isActive ? 'filter-item--active' : ''}`}
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
        <div className="filter-list" style={{ maxHeight: 240, overflowY: 'auto' }}>
          <button
            className={`filter-item ${source === null ? 'filter-item--active' : ''}`}
            onClick={() => onSourceChange(null)}
          >
            <span className="filter-item__label">Alle Quellen</span>
            <span className="filter-item__count">{counts.source?.__all ?? ''}</span>
          </button>
          {Object.entries(counts.source || {})
            .filter(([key]) => key !== '__all')
            .sort((a, b) => b[1] - a[1])
            .map(([name, count]) => {
              const isActive = source === name
              const muted    = prefs.mutedSources.includes(name)
              return (
                <div key={name} className="filter-item-row">
                  <button
                    className={`filter-item ${isActive ? 'filter-item--active' : ''} ${muted ? 'filter-item--muted' : ''}`}
                    onClick={() => onSourceChange(name)}
                  >
                    <span className="filter-item__label">{name}</span>
                    <span className="filter-item__count">{count}</span>
                  </button>
                  <button
                    className="filter-item__mute"
                    onClick={() => onToggleSource(name)}
                    title={muted ? 'Quelle wieder anzeigen' : 'Quelle ausblenden'}
                  >
                    {muted ? '🔇' : '·'}
                  </button>
                </div>
              )
          })}
        </div>
      </div>
    </aside>
  )
}
