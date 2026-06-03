import { useEffect, useRef, useState, useMemo } from "react"
import axios from "axios"
import NewsCard from "../components/NewsCard"
import NewsRow from "../components/NewsRow"
import FilterSidebar from "../components/FilterSidebar"
import PlatformSwitcher from "../components/PlatformSwitcher"
import { detectTopics, topicLabel } from "../utils/topics"
import { usePrefs } from "../hooks/usePrefs"

const PAGE_SIZE = 30

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------
function isNewer(article, since) {
  if (!since) return false
  const ts = article.published_at || article.fetched_at
  return ts ? ts > since : false
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------
function StatPill({ mod, label, value }) {
  return (
    <div className={`stat-pill stat-pill--${mod}`}>
      <span className="stat-pill__value">{value ?? 0}</span>
      <span className="stat-pill__label">{label}</span>
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

function ErrorState({ message }) {
  return (
    <div className="state state--error">
      <div className="state__icon">⚠️</div>
      <div className="state__title">Fehler beim Laden</div>
      <div>{message}</div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="state">
      <div className="state__icon">🔍</div>
      <div className="state__title">Keine Artikel gefunden</div>
      <div>Filtereinstellungen anpassen oder Suche leeren.</div>
    </div>
  )
}

function ResultsBar({ count, total, filters, onClear, onMarkAllVisible, visibleIds }) {
  const chips = []
  if (filters.search)   chips.push({ key: "search",   label: `"${filters.search}"`,   onClear: onClear.search })
  if (filters.category) chips.push({ key: "category", label: filters.category,         onClear: onClear.category })
  if (filters.topic)    chips.push({ key: "topic",    label: topicLabel(filters.topic), onClear: onClear.topic })
  if (filters.source)   chips.push({ key: "source",   label: filters.source,           onClear: onClear.source })

  return (
    <div className="results-bar">
      <span className="results-bar__count">
        {count} {count === total ? "Artikel" : `von ${total} Artikeln`}
      </span>
      {chips.map(c => (
        <button key={c.key} className="filter-chip" onClick={c.onClear}>
          {c.label} <span aria-hidden>×</span>
        </button>
      ))}
      <button className="mark-all-btn" onClick={() => onMarkAllVisible(visibleIds)}>
        ✓ Alle gelesen
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
export default function Dashboard() {
  const [allArticles, setAllArticles] = useState([])
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(null)

  // Session filters
  const [search, setSearch]     = useState("")
  const [category, setCategory] = useState(null)
  const [topic, setTopic]       = useState(null)
  const [source, setSource]     = useState(null)
  const [page, setPage]         = useState(1)

  // lastVisit for "new" calculation (stable across renders)
  const prevVisitRef = useRef(null)

  const {
    prefs,
    toggleTopic, toggleSource,
    setShowOffTopic, setShowDump, resetPrefs,
    setSelectedPlatform,
    markRead, markAllRead, isRead,
    touchVisit,
  } = usePrefs()

  // On mount: record visit + fetch articles
  useEffect(() => {
    prevVisitRef.current = touchVisit()
    setLoading(true)
    axios.get("/api/news", { params: { page: 1, page_size: 500 } })
      .then(res => {
        const items = (res.data.items || []).map(a => ({
          ...a,
          _topics: (a.topics && a.topics.length) ? a.topics : detectTopics(a),
        }))
        setAllArticles(items)
      })
      .catch(() => setError("Nachrichten konnten nicht geladen werden."))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { setPage(1) }, [search, category, topic, source, prefs.selectedPlatform, prefs.showOffTopic, prefs.showDump])

  // 1. Basis-Filter (Prefs: OFF_TOPIC / DUMP / Mute / Topics)
  const visibleArticles = useMemo(() => {
    return allArticles.filter(a => {
      const cat = a.category || "NORMAL"
      if (cat === "OFF_TOPIC" && !prefs.showOffTopic) return false
      if (cat === "DUMP"      && !prefs.showDump)     return false
      if (prefs.mutedSources.includes(a.source))      return false
      if (prefs.subscribedTopics.length > 0 && cat !== "KRITISCH") {
        if (!a._topics.some(t => prefs.subscribedTopics.includes(t))) return false
      }
      return true
    })
  }, [allArticles, prefs.showOffTopic, prefs.showDump, prefs.mutedSources, prefs.subscribedTopics])

  // 2. Plattform-Filter (selectedPlatform + cross)
  const platformFiltered = useMemo(() => {
    const sel = prefs.selectedPlatform || "all"
    if (sel === "all") return visibleArticles
    return visibleArticles.filter(a => {
      const plat = a.platform ?? "cross"
      return plat === sel || plat === "cross"
    })
  }, [visibleArticles, prefs.selectedPlatform])

  // 3. Session-Filter (Suche, Kategorie, Topic, Source)
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return platformFiltered.filter(a => {
      if (category && a.category !== category)     return false
      if (topic    && !a._topics.includes(topic))  return false
      if (source   && a.source !== source)         return false
      if (q) {
        const hay = `${a.title} ${a.source} ${a.summary || ""}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
  }, [platformFiltered, search, category, topic, source])

  // 4. Sortierung: KRITISCH zuerst, dann published_at DESC
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const aPri = a.category === "KRITISCH" ? 0 : 1
      const bPri = b.category === "KRITISCH" ? 0 : 1
      if (aPri !== bPri) return aPri - bPri
      const aT = a.published_at || ""
      const bT = b.published_at || ""
      return bT.localeCompare(aT)
    })
  }, [filtered])

  // Split into KRITISCH / rest
  const kritischItems = useMemo(() => sorted.filter(a => a.category === "KRITISCH"), [sorted])
  const restItems     = useMemo(() => sorted.filter(a => a.category !== "KRITISCH"), [sorted])

  // Counts
  const counts = useMemo(() => {
    const cat = { all: allArticles.length, KRITISCH: 0, NORMAL: 0, DUMP: 0, OFF_TOPIC: 0, PENDING: 0 }
    const top = { __all: allArticles.length }
    const src = { __all: allArticles.length }
    const plat = { all: allArticles.length, windows: 0, apple: 0, android: 0, cross: 0 }
    for (const a of allArticles) {
      const c = a.category || "NORMAL"
      cat[c] = (cat[c] || 0) + 1
      for (const t of a._topics) top[t] = (top[t] || 0) + 1
      src[a.source] = (src[a.source] || 0) + 1
      const p = a.platform ?? "cross"
      plat[p] = (plat[p] || 0) + 1
    }
    return { category: cat, topic: top, source: src, platform: plat }
  }, [allArticles])

  // "Neu"-Stats
  const newCount      = useMemo(() =>
    sorted.filter(a => isNewer(a, prevVisitRef.current) && !isRead(a.id)).length,
  // isRead is a closure — recompute when prefs.readIds changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  [sorted, prefs.readIds])

  const openKritisch  = useMemo(() =>
    kritischItems.filter(a => !isRead(a.id)).length,
  // eslint-disable-next-line react-hooks/exhaustive-deps
  [kritischItems, prefs.readIds])

  const hasActiveFilters = !!(search || category || topic || source)

  // Pagination for "rest" section only
  const totalPages = Math.max(1, Math.ceil(restItems.length / PAGE_SIZE))
  const pageRest   = restItems.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  function resetFilters() {
    setSearch(""); setCategory(null); setTopic(null); setSource(null)
  }

  const visibleIds = useMemo(() => sorted.map(a => a.id), [sorted])

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
          <StatPill mod="kritisch" label="Neu"      value={newCount} />
          <StatPill mod="normal"   label="Kritisch" value={openKritisch} />
        </div>
      </header>

      {/* Platform Switcher — below header, full width */}
      <div style={{ padding: "var(--s-3) var(--s-6) 0", maxWidth: "var(--content-max)", margin: "0 auto", width: "100%" }}>
        <PlatformSwitcher
          value={prefs.selectedPlatform || "all"}
          onChange={setSelectedPlatform}
          counts={counts.platform}
        />
      </div>

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
          selectedPlatform={prefs.selectedPlatform}
          onSetSelectedPlatform={setSelectedPlatform}
        />

        <section className="content">
          <ResultsBar
            count={filtered.length}
            total={visibleArticles.length}
            filters={{ search, category, topic, source }}
            onClear={{
              search:   () => setSearch(""),
              category: () => setCategory(null),
              topic:    () => setTopic(null),
              source:   () => setSource(null),
            }}
            onMarkAllVisible={markAllRead}
            visibleIds={visibleIds}
          />

          {loading && <SkeletonGrid />}
          {error   && <ErrorState message={error} />}

          {!loading && !error && (
            <>
              {/* ---- Sektion A: KRITISCH ---- */}
              <div className="section-head section-head--kritisch">
                <span className="section-head__title">Sofort prüfen</span>
                {kritischItems.length > 0 && (
                  <span className="section-head__count">{kritischItems.length}</span>
                )}
              </div>

              {kritischItems.length === 0 ? (
                <p style={{ color: "var(--gema-muted)", fontSize: "var(--t-sm)", marginBottom: "var(--s-5)" }}>
                  Aktuell nichts Kritisches.
                </p>
              ) : (
                <div className="news-grid" style={{ marginBottom: "var(--s-8)" }}>
                  {kritischItems.map(a => (
                    <NewsCard
                      key={a.id}
                      article={a}
                      isNew={isNewer(a, prevVisitRef.current) && !isRead(a.id)}
                      isRead={isRead(a.id)}
                      onMarkRead={markRead}
                    />
                  ))}
                </div>
              )}

              {/* ---- Sektion B: Übrige (dichte Liste) ---- */}
              {restItems.length > 0 && (
                <>
                  <div className="section-head section-head--normal">
                    <span className="section-head__title">Übrige</span>
                    <span className="section-head__count" style={{ background: "var(--gema-bg-alt)", color: "var(--gema-text-soft)" }}>
                      {restItems.length}
                    </span>
                  </div>

                  {pageRest.length === 0 && <EmptyState />}

                  <div className="news-rows">
                    {pageRest.map(a => (
                      <NewsRow
                        key={a.id}
                        article={a}
                        isNew={isNewer(a, prevVisitRef.current) && !isRead(a.id)}
                        isRead={isRead(a.id)}
                        onMarkRead={markRead}
                      />
                    ))}
                  </div>

                  {totalPages > 1 && (
                    <nav className="pagination" aria-label="Seitennavigation">
                      <button className="pagination__btn"
                              onClick={() => setPage(p => Math.max(1, p - 1))}
                              disabled={page === 1}>← Zurück</button>
                      <span className="pagination__info">Seite {page} / {totalPages}</span>
                      <button className="pagination__btn"
                              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                              disabled={page === totalPages}>Weiter →</button>
                    </nav>
                  )}
                </>
              )}

              {sorted.length === 0 && <EmptyState />}
            </>
          )}
        </section>
      </div>
    </>
  )
}
