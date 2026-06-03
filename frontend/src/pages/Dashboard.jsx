/**
 * K3/K5/K4 — Dashboard: Triage-Board mit zwei Sektionen.
 * K3: "Sofort prüfen" (KRITISCH) + "Übrige" (NORMAL) als getrennte Sektionen.
 * K5: counts.all = total aus Hauptabfrage; fetchCounts mit collapse:true.
 * K4: selectMode-Zustand; Checkboxen erst sichtbar wenn aktiv.
 */
import { useCallback, useEffect, useRef, useState } from "react"
import axios from "axios"
import Topbar   from "../components/Topbar"
import NewsRow  from "../components/NewsRow"
import { useUIPrefs }   from "../hooks/useUIPrefs"
import { useReadState } from "../hooks/useReadState"

const PAGE_SIZE    = 30
const API_BASE     = "/api"
const CURRENT_USER = "anonymous"

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

// K5: collapse:true damit Zähler mit Hauptabfrage übereinstimmt
async function fetchCounts(view) {
  const platforms = ["all", "windows", "apple", "android"]
  const results   = await Promise.allSettled(
    platforms.map(p =>
      axios.get(`${API_BASE}/news`, {
        params: {
          view, page: 1, page_size: 1, collapse: true,
          ...(p !== "all" ? { platform: p } : {}),
        },
      }).then(r => [p, r.data.total ?? 0])
    )
  )
  const counts = {}
  for (const r of results) {
    if (r.status === "fulfilled") counts[r.value[0]] = r.value[1]
  }
  return counts
}

export default function Dashboard({ onKritischCount }) {
  const { prefs, setPlatform, setView, touchVisit } = useUIPrefs()
  const { readMap, isRead, markRead, markUnread, markBulk, initReadMap } =
    useReadState(CURRENT_USER)

  const [items,      setItems]      = useState([])
  const [total,      setTotal]      = useState(0)
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)
  const [counts,     setCounts]     = useState({ all: 0, windows: 0, apple: 0, android: 0 })
  const [q,          setQ]          = useState("")
  const [topic,      setTopic]      = useState(null)
  const [source,     setSource]     = useState(null)
  const [page,       setPage]       = useState(1)
  const [showDump,   setShowDump]   = useState(false)
  const [selectMode, setSelectMode] = useState(false)

  const prevVisitRef = useRef(null)
  const [focusIdx, setFocusIdx] = useState(-1)
  const [selected, setSelected] = useState(new Set())
  const listRef   = useRef(null)
  const searchRef = useRef(null)
  const seqRef    = useRef("")

  useEffect(() => {
    prevVisitRef.current = touchVisit()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
        const fetchedTotal = res.data.total ?? 0
        setItems(articleItems)
        setTotal(fetchedTotal)
        // K5: aktuelles Segment-Counts direkt aus Hauptabfrage
        setCounts(prev => ({ ...prev, [prefs.platform]: fetchedTotal }))
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
  useEffect(() => { setPage(1) }, [prefs.view, prefs.platform, q, topic, source])

  useEffect(() => {
    fetchCounts(prefs.view).then(setCounts).catch(() => {})
  }, [prefs.view])

  const kritischUnread = items.filter(a => a.category === "KRITISCH" && !isRead(a.id)).length
  useEffect(() => {
    document.title = kritischUnread > 0 ? `(${kritischUnread}) IT News` : "IT News"
    onKritischCount?.(kritischUnread)
  }, [kritischUnread, isRead, onKritischCount])

  // K3: Sektionen
  const mainItems    = items.filter(a => a.category !== "DUMP" && a.category !== "OFF_TOPIC")
  const dumpItems    = items.filter(a => a.category === "DUMP"  || a.category === "OFF_TOPIC")
  const kritischItems = mainItems.filter(a => a.category === "KRITISCH")
  const normalItems   = mainItems.filter(a => a.category !== "KRITISCH")
  // Reihenfolge muss DOM-Reihenfolge = focusIdx-Reihenfolge entsprechen
  const visibleItems = showDump ? [...mainItems, ...dumpItems] : mainItems

  // Keyboard shortcuts
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
          if (selected.size > 0) { markBulk(Array.from(selected)); setSelected(new Set()) }
          else if (focused) markRead(focused.id)
          break
        case "u":
          if (focused) markUnread(focused.id)
          break
        case "t":
          if (focused) {
            const haloUrl = import.meta.env.VITE_HALO_TICKET_BASE_URL
            if (haloUrl) window.open(
              `${haloUrl}?summary=${encodeURIComponent(focused.title)}&note=${encodeURIComponent(focused.url ?? "")}`,
              "_blank", "noopener,noreferrer"
            )
          }
          break
        case "Escape":
          if (selectMode) { setSelectMode(false); setSelected(new Set()) }
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
  }, [focusIdx, visibleItems, selected, selectMode])

  useEffect(() => {
    if (!listRef.current || focusIdx < 0) return
    listRef.current.querySelectorAll("[data-id]")[focusIdx]?.scrollIntoView({
      block: "nearest", behavior: "smooth",
    })
  }, [focusIdx])

  function handleRowSelect(idx, e) {
    if (!e.shiftKey && !selectMode) return
    e.preventDefault()
    if (!selectMode) setSelectMode(true)
    const id = visibleItems[idx]?.id
    if (!id) return
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function renderRow(a, idx) {
    return (
      <NewsRow
        key={a.id}
        article={a}
        isNew={!!(prevVisitRef.current && (a.published_at ?? "") > prevVisitRef.current)}
        isRead={isRead(a.id)}
        readBy={readMap[a.id] ?? a.read_by ?? []}
        isFocused={focusIdx === idx}
        selected={selected.has(a.id)}
        selectMode={selectMode}
        onMarkRead={()   => markRead(a.id)}
        onMarkUnread={()  => markUnread(a.id)}
        onSelect={e      => handleRowSelect(idx, e)}
        onSourceClick={s => { setSource(s); setPage(1) }}
        onTopicClick={t  => { setTopic(t);  setPage(1) }}
      />
    )
  }

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
        {!selectMode && (
          <button
            className="results-bar__select-btn"
            onClick={() => setSelectMode(true)}
          >
            Auswählen
          </button>
        )}
        {selectMode && (
          <>
            <span className="results-bar__select-hint">
              {selected.size > 0
                ? `${selected.size} ausgewählt`
                : "Shift+Klick zum Auswählen"}
            </span>
            {selected.size > 0 && (
              <button
                className="mark-all-btn"
                onClick={() => { markBulk(Array.from(selected)); setSelected(new Set()) }}
              >
                &#x2713; {selected.size} gelesen
              </button>
            )}
            <button
              className="results-bar__cancel-btn"
              onClick={() => { setSelectMode(false); setSelected(new Set()) }}
            >
              Abbrechen
            </button>
          </>
        )}
        {!loading && !selectMode && total > 0 && prefs.view === "unread" && (
          <button className="mark-all-btn" onClick={() => markBulk(items.map(a => a.id))}>
            Alle gelesen
          </button>
        )}
      </div>

      {/* K3: Zwei Sektionen */}
      <div ref={listRef}>
        {loading && <SkeletonRows />}
        {!loading && error && <ErrorState message={error} onRetry={doFetch} />}

        {!loading && !error && (
          <>
            {/* Sektion 1: Sofort prüfen (KRITISCH) */}
            <div className="triage-section">
              <div className={`triage-section__head${kritischItems.length > 0 ? " triage-section__head--kritisch" : ""}`}>
                <span className={`triage-dot${kritischItems.length > 0 ? " triage-dot--rot" : ""}`} />
                <span>Sofort prüfen</span>
                <span className={`triage-count${kritischItems.length > 0 ? " triage-count--rot" : ""}`}>
                  {kritischItems.length}
                </span>
              </div>
              {kritischItems.length === 0 ? (
                <div className="triage-empty">Aktuell nichts Kritisches.</div>
              ) : (
                <div className="news-list">
                  {kritischItems.map(a =>
                    renderRow(a, visibleItems.indexOf(a))
                  )}
                </div>
              )}
            </div>

            {/* Sektion 2: Übrige (NORMAL) */}
            {normalItems.length > 0 && (
              <div className="triage-section">
                <div className="triage-section__head">
                  <span className="triage-dot" />
                  <span>Übrige</span>
                  <span className="triage-count">
                    {normalItems.length}
                    {page < totalPages ? "+" : ""}
                  </span>
                </div>
                <div className="news-list">
                  {normalItems.map(a =>
                    renderRow(a, visibleItems.indexOf(a))
                  )}
                </div>
              </div>
            )}

            {/* DUMP am Ende */}
            {showDump && dumpItems.length > 0 && (
              <div className="triage-section">
                <div className="triage-section__head">
                  <span className="triage-dot" />
                  <span>Aussortiert</span>
                  <span className="triage-count">{dumpItems.length}</span>
                </div>
                <div className="news-list">
                  {dumpItems.map(a =>
                    renderRow(a, visibleItems.indexOf(a))
                  )}
                </div>
              </div>
            )}

            {/* Leer-State */}
            {mainItems.length === 0 && dumpItems.length === 0 && (
              <div className="state">
                {prefs.view === "unread"
                  ? <><div className="state__icon">&#x1F389;</div><div className="state__title">Alles gelesen!</div><div className="state__msg">Nichts Neues — gut gemacht.</div></>
                  : <><div className="state__icon">&#x1F50D;</div><div className="state__title">Keine Treffer</div><div className="state__msg">Filter oder Suche anpassen.</div></>
                }
              </div>
            )}
          </>
        )}
      </div>

      {/* Dump-Toggle */}
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
