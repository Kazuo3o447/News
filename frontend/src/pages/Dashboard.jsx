import { useEffect, useState, useMemo } from 'react'
import axios from 'axios'
import NewsCard from '../components/NewsCard'
import FilterSidebar from '../components/FilterSidebar'
import { detectTopics, topicLabel } from '../utils/topics'
import { usePrefs } from '../hooks/usePrefs'

const PAGE_SIZE = 24

export default function Dashboard() {
  const [allArticles, setAllArticles] = useState([])
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(null)

  // Filter-State (Session)
  const [search, setSearch]     = useState('')
  const [category, setCategory] = useState(null)
  const [topic, setTopic]       = useState(null)
  const [source, setSource]     = useState(null)
  const [page, setPage]         = useState(1)

  // Personalisierung (persistent)
  const {
    prefs,
    toggleTopic, toggleSource,
    setShowOffTopic, setShowDump,
    resetPrefs,
  } = usePrefs()

  useEffect(() => {
    setLoading(true)
    axios.get('/api/news', { params: { page: 1, page_size: 500 } })
      .then(res => {
        const items = (res.data.items || []).map(a => ({
          ...a,
          // Topics aus Backend bevorzugen, falls leer: Client-Fallback
          _topics: (a.topics && a.topics.length) ? a.topics : detectTopics(a),
        }))
        setAllArticles(items)
      })
      .catch(() => setError('Nachrichten konnten nicht geladen werden.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { setPage(1) }, [search, category, topic, source, prefs])

  // 1. Personalisierte Basis (OFF_TOPIC / DUMP / Topic-Subscription / Source-Mute)
  const visibleArticles = useMemo(() => {
    return allArticles.filter(a => {
      const cat = a.category || 'NORMAL'
      if (cat === 'OFF_TOPIC' && !prefs.showOffTopic) return false
      if (cat === 'DUMP'      && !prefs.showDump)    return false
      if (prefs.mutedSources.includes(a.source))     return false

      // Topic-Subscription: Artikel muss mindestens 1 abonniertes Topic haben.
      // Ausnahme: KRITISCH wird immer angezeigt (Security-Tier-1).
      if (prefs.subscribedTopics.length > 0 && cat !== 'KRITISCH') {
        const hit = a._topics.some(t => prefs.subscribedTopics.includes(t))
        if (!hit) return false
      }
      return true
    })
  }, [allArticles, prefs])

  // 2. Session-Filter (Suche, Kategorie, Topic, Source)
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return visibleArticles.filter(a => {
      if (category && a.category !== category)        return false
      if (topic    && !a._topics.includes(topic))     return false
      if (source   && a.source !== source)            return false
      if (q) {
        const hay = `${a.title} ${a.source} ${a.summary || ''}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
  }, [visibleArticles, search, category, topic, source])

  // Counts auf Basis aller Artikel (damit auch versteckte/off-topic zählbar bleiben)
  const counts = useMemo(() => {
    const cat = { all: allArticles.length, KRITISCH: 0, NORMAL: 0, DUMP: 0, OFF_TOPIC: 0 }
    const top = { __all: allArticles.length }
    const src = { __all: allArticles.length }
    for (const a of allArticles) {
      const c = a.category || 'NORMAL'
      cat[c] = (cat[c] || 0) + 1
      for (const t of a._topics) top[t] = (top[t] || 0) + 1
      src[a.source] = (src[a.source] || 0) + 1
    }
    return { category: cat, topic: top, source: src }
  }, [allArticles])

  const hasActiveFilters = !!(search || category || topic || source)
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageItems  = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  function resetFilters() {
    setSearch(''); setCategory(null); setTopic(null); setSource(null)
  }

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-head__title">
            <span className="page-head__title-accent" />
            IT-Nachrichten
          </h1>
          <p className="page-head__subtitle">
            {visibleArticles.length} relevante von {allArticles.length} Artikeln · KI-vorsortiert
          </p>
        </div>
        <div className="page-head__stats">
          <StatPill mod="kritisch" label="Kritisch" value={counts.category.KRITISCH} />
          <StatPill mod="normal"   label="Normal"   value={counts.category.NORMAL} />
          <StatPill mod="dump"     label="Dump"     value={counts.category.DUMP} />
        </div>
      </header>

      <div className="layout">
        <FilterSidebar
          search={search}     onSearchChange={setSearch}
          category={category} onCategoryChange={setCategory}
          topic={topic}       onTopicChange={setTopic}
          source={source}     onSourceChange={setSource}
          counts={counts}
          hasActiveFilters={hasActiveFilters}
          onReset={resetFilters}
          prefs={prefs}
          onToggleTopic={toggleTopic}
          onToggleSource={toggleSource}
          onSetShowOffTopic={setShowOffTopic}
          onSetShowDump={setShowDump}
        />

        <section className="content">
          <ResultsBar
            count={filtered.length}
            total={visibleArticles.length}
            filters={{ search, category, topic, source }}
            onClear={{
              search:   () => setSearch(''),
              category: () => setCategory(null),
              topic:    () => setTopic(null),
              source:   () => setSource(null),
            }}
          />

          {loading && <SkeletonGrid />}
          {error   && <ErrorState message={error} />}
          {!loading && !error && pageItems.length === 0 && <EmptyState />}
          {!loading && !error && pageItems.length > 0 && (
            <>
              <div className="news-grid">
                {pageItems.map(a => <NewsCard key={a.id} article={a} />)}
              </div>
              {totalPages > 1 && (
                <nav className="pagination" aria-label="Seitennavigation">
                  <button className="pagination__btn"
                          onClick={() => setPage(p => Math.max(1, p - 1))}
                          disabled={page === 1}>← Zurück</button>
                  <span className="pagination__info">Seite {page} von {totalPages}</span>
                  <button className="pagination__btn"
                          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                          disabled={page === totalPages}>Weiter →</button>
                </nav>
              )}
            </>
          )}
        </section>
      </div>
    </>
  )
}

function ResultsBar({ count, total, filters, onClear }) {
  const chips = []
  if (filters.search)   chips.push({ key: 'search',   label: `Suche: "${filters.search}"` })
  if (filters.category) chips.push({ key: 'category', label: filters.category })
  if (filters.topic)    chips.push({ key: 'topic',    label: topicLabel(filters.topic) })
  if (filters.source)   chips.push({ key: 'source',   label: filters.source })

  return (
    <div className="results-bar">
      <div>
        <span className="results-bar__count">{count}</span>
        {count !== total && <span> von {total}</span>} Artikel
      </div>
      {chips.length > 0 && (
        <div className="active-filters">
          {chips.map(c => (
            <span key={c.key} className="chip">
              {c.label}
              <button className="chip__remove" onClick={onClear[c.key]} aria-label="Filter entfernen">×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function StatPill({ mod, label, value }) {
  return (
    <div className={`stat-pill stat-pill--${mod}`}>
      <span className="stat-pill__dot" />
      <div>
        <div className="stat-pill__label">{label}</div>
        <div className="stat-pill__value">{value ?? '–'}</div>
      </div>
    </div>
  )
}

function SkeletonGrid() {
  return (
    <div className="skeleton-grid">
      {Array.from({ length: 6 }).map((_, i) => <div key={i} className="skeleton-card" />)}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="state">
      <div className="state__icon">✉</div>
      <div className="state__title">Keine Treffer</div>
      <div>Für die gewählte Filterkombination wurden keine Artikel gefunden.</div>
    </div>
  )
}

function ErrorState({ message }) {
  return (
    <div className="state state--error">
      <div className="state__icon">!</div>
      <div className="state__title">Fehler beim Laden</div>
      <div>{message}</div>
    </div>
  )
}
