/**
 * F6 — Dashboard: Triage-UI für IT-Admin-Team.
 * Server-seitige Filter (view, platform, q, topic, source, page).
 * Tastatur-Triage j/k/o/e/u/t//, F3.
 * Team Read-State via useReadState (F4).
 * UI-Vorlieben (platform, view, darkMode) via useUIPrefs (F4).
 */
import { useCallback, useEffect, useRef, useState } from "react"
import axios from "axios"
import Topbar   from "../components/Topbar"
import NewsRow  from "../components/NewsRow"
import { useUIPrefs }   from "../hooks/useUIPrefs"
import { useReadState } from "../hooks/useReadState"

const PAGE_SIZE    = 30
const API_BASE     = "/api"
const CURRENT_USER = "anonymous" // X-MS-CLIENT-PRINCIPAL-NAME is resolved server-side

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------
function SkeletonRows() {
  return (
    <div className="skeleton-list">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className={`skeleton-row${i < 2 ? " skeleton-row--tall" : ""}`} />
      ))}
    </div>
  )
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="state state--error">
      <div className="state__icon">&#x26A0;</div>
      <div className="state__title">Verbindungsfehler</div>
      <div className="state__msg">{message}</div>
      <button className="state__btn" onClick={onRetry}>Erneut laden</button>
    </div>
  )
}

function EmptyState({ view }) {
  if (view === "unread") return (
    <div className="state">
      <div className="state__icon">&#x1F389;</div>
      <div className="state__title">Alles gelesen!</div>
      <div className="state__msg">Nichts Neues — gut gemacht.</div>
    </div>
  )
  return (
    <div className="state">
      <div className="state__icon">&#x1F50D;</div>
      <div className="state__title">Keine Treffer</div>
      <div className="state__msg">Filter oder Suche anpassen.</div>
    </div>
  )
}

// Aggregated per-platform counts (for PlatformSwitcher badges)
async function fetchCounts(view) {
  const platforms = ["all", "windows", "apple", "android"]
  const results   = await Promise.allSettled(
    platforms.map(p =>
      axios.get(`${API_BASE}/news`, {
        params: { view, page: 1, page_size: 1, ...(p !== "all" ? { platform: p } : {}) },
      }).then(r => [p, r.data.total ?? 0])
    )
  )
  const counts = {}
  for (const r of results) {
    if (r.status === "fulfilled") counts[r.value[0]] = r.value[1]
  }
  return counts
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
export default function Dashboard({ onKritischCount }) {
  const { prefs, setPlatform, setView, touchVisit } = useUIPrefs()
  const { readMap, isRead, markRead, markUnread, markBulk, initReadMap } =
    useReadState(CURRENT_USER)

  // Server state
  const [items,    setItems]    = useState([])
  const [total,    setTotal]    = useState(0)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [counts,   setCounts]   = useState({ all: 0, windows: 0, apple: 0, android: 0 })

  // Filter state
  const [q,        setQ]        = useState("")
  const [topic,    setTopic]    = useState(null)
  const [source,   setSource]   = useState(null)
  const [page,     setPage]     = useState(1)
  const [showDump, setShowDump] = useState(false)

  // "neu seit letztem Besuch"
  const prevVisitRef = useRef(null)

  // Keyboard focus (F3)
  const [focusIdx, setFocusIdx] = useState(-1)
  const [selected, setSelected] = useState(new Set())
  const listRef   = useRef(null)
  const searchRef = useRef(null)
  const seqRef    = useRef("")

  // ---------------------------------------------------------------------------
  // Mount: record visit
  // ---------------------------------------------------------------------------
  useEffect(() => {
    prevVisitRef.current = touchVisit()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---------------------------------------------------------------------------
  // Fetch articles
  // ---------------------------------------------------------------------------
  const doFetch = useCallback(() => {
    setLoading(true)
    setError(null)
    const params = {
      view:      prefs.view,
      page,
      page_size: PAGE_SIZE,
      collapse:  true,
      ...(prefs.platform !== "all" ? { platform: prefs.platform } : {}),
      ...(q      ? { q }      : {}),
      ...(topic  ? { topic }  : {}),
      ...(source ? { source } : {}),
    }
    axios.get(`${API_BASE}/news`, { params })
      .then(res => {
        const articleItems = (res.data.items ?? []).map(a => ({
          ...a,
          topics: a.topics ?? [],
        }))
        setItems(articleItems)
        setTotal(res.data.total ?? 0)
        if (focusIdx < 0 && articleItems.length > 0) setFocusIdx(0)
        initReadMap(articleItems)
      })
      .catch(err =>
        setError(err?.response?.data?.detail ?? "Nachrichten konnten nicht geladen werden.")
      )
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefs.view, prefs.platform, q, topic, source, page])

  useEffect(() => { doFetch() }, [doFetch])

  // Reset page on filter/view change
  useEffect(() => { setPage(1) }, [prefs.view, prefs.platform, q, topic, source])

  // Refresh platform counts
  useEffect(() => {
    fetchCounts(prefs.view).then(setCounts).catch(() => {})
  }, [prefs.view])

  // Tab title + notify parent
  const kritischUnread = items.filter(a => a.category === "KRITISCH" && !isRead(a.id)).length
  useEffect(() => {
    document.title = kritischUnread > 0 ? `(${kritischUnread}) IT News` : "IT News"
    onKritischCount?.(kritischUnread)
  }, [kritischUnread, isRead, onKritischCount])

  // Split: main vs dump
  const mainItems = items.filter(a => a.category !== "DUMP" && a.category !== "OFF_TOPIC")
  const dumpItems = items.filter(a => a.category === "DUMP" || a.category === "OFF_TOPIC")
  const visibleItems = showDump ? items : mainItems

  // ---------------------------------------------------------------------------
  // Keyboard shortcuts (F3)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    function onKey(e) {
      const tag = document.activeElement?.tagName
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
        if (e.key === "Escape") document.activeElement.blur()
        return
      }
      const focused = visibleItems[focusIdx]

      if (e.key === "g" && !seqRef.current) {
        seqRef.current = "g"
        setTimeout(() => { seqRef.current = "" }, 800)
        return
      }
      if (seqRef.current === "g") {
        seqRef.current = ""
        if (e.key === "u") { setView("unread"); return }
        if (e.key === "a") { setView("all");    return }
      }

      switch (e.key) {
        case "j": case "ArrowDown":
          e.preventDefault()
          setFocusIdx(i => Math.min(visibleItems.length - 1, i + 1))
          break
        case "k": case "ArrowUp":
          e.preventDefault()
          setFocusIdx(i => Math.max(0, i - 1))
          break
        case "o": case "Enter":
          if (focused?.url) window.open(focused.url, "_blank", "noopener,noreferrer")
          break
        case "e":
          if (selected.size > 0) {
            markBulk(Array.from(selected))
            setSelected(new Set())
          } else if (focused) {
            markRead(focused.id)
          }
          break
        case "u":
          if (focused) markUnread(focused.id)
          break
        case "t":
          if (focused) {
            const haloUrl = import.meta.env.VITE_HALO_TICKET_BASE_URL
            if (haloUrl) {
              const href = `${haloUrl}?summary=${encodeURIComponent(focused.title)}&note=${encodeURIComponent(focused.url ?? "")}`
              window.open(href, "_blank", "noopener,noreferrer")
            }
          }
          break
        case "/":
          e.preventDefault()
          searchRef.current?.focus()
          break
        default:
          break
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusIdx, visibleItems, selected])

  // Scroll focused row into view
  useEffect(() => {
    if (!listRef.current || focusIdx < 0) return
    listRef.current.querySelectorAll("[data-id]")[focusIdx]?.scrollIntoView({
      block: "nearest", behavior: "smooth",
    })
  }, [focusIdx])

  // ---------------------------------------------------------------------------
  // Bulk selection via Shift-click
  // ---------------------------------------------------------------------------
  function handleRowSelect(idx, e) {
    if (!e.shiftKey) return
    e.preventDefault()
    const id = visibleItems[idx]?.id
    if (!id) return
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="dashboard">
      <Topbar
        platform={prefs.platform}
        onPlatformChange={p => { setPlatform(p); setPage(1) }}
        platformCounts={counts}
        search={q}
        onSearchChange={v => { setQ(v); setPage(1) }}
        view={prefs.view}
        onViewChange={v => { setView(v); setPage(1) }}
        topic={topic}
        onTopicClear={() => { setTopic(null); setPage(1) }}
        source={source}
        onSourceClear={() => { setSource(null); setPage(1) }}
        searchRef={searchRef}
      />

      {/* Results bar */}
      <div className="results-bar">
        <span className="results-bar__count">
          {loading ? "\u2026" : `${total} Artikel`}
        </span>
        {selected.size > 0 && (
          <button
            className="mark-all-btn"
            onClick={() => { markBulk(Array.from(selected)); setSelected(new Set()) }}
          >
            &#x2713; {selected.size} als gelesen
          </button>
        )}
        {!loading && total > 0 && selected.size === 0 && prefs.view === "unread" && (
          <button className="mark-all-btn" onClick={() => markBulk(items.map(a => a.id))}>
            Alle gelesen
          </button>
        )}
      </div>

      {/* Article list */}
      <div className="news-list" ref={listRef}>
        {loading && <SkeletonRows />}
        {!loading && error   && <ErrorState message={error} onRetry={doFetch} />}
        {!loading && !error && visibleItems.length === 0 && <EmptyState view={prefs.view} />}

        {!loading && !error && visibleItems.map((a, idx) => (
          <NewsRow
            key={a.id}
            article={a}
            isNew={!!(prevVisitRef.current && (a.published_at ?? "") > prevVisitRef.current)}
            isRead={isRead(a.id)}
            readBy={readMap[a.id] ?? a.read_by ?? []}
            isFocused={focusIdx === idx}
            selected={selected.has(a.id)}
            onMarkRead={()   => markRead(a.id)}
            onMarkUnread={()  => markUnread(a.id)}
            onSelect={e      => handleRowSelect(idx, e)}
            onSourceClick={s => { setSource(s); setPage(1) }}
            onTopicClick={t  => { setTopic(t);  setPage(1) }}
          />
        ))}
      </div>

      {/* Dump toggle */}
      {!loading && !error && dumpItems.length > 0 && (
        <button
          className={`dump-toggle${showDump ? " dump-toggle--open" : ""}`}
          onClick={() => setShowDump(v => !v)}
        >
          {showDump
            ? `Aussortierte ausblenden \u25B2`
            : `${dumpItems.length} aussortierte Meldungen anzeigen \u25BC`}
        </button>
      )}

      {/* Pagination */}
      {!loading && !error && totalPages > 1 && (
        <nav className="pagination" aria-label="Seitennavigation">
          <button
            className="pagination__btn"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            &#x2190; Zurück
          </button>
          <span className="pagination__info">Seite {page}&nbsp;/&nbsp;{totalPages}</span>
          <button
            className="pagination__btn"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Weiter &#x2192;
          </button>
        </nav>
      )}
    </div>
  )
}
