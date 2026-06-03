/**
 * K2/K1/K4/K6 — NewsRow: klassifizierte Triage-Zeile.
 * K1: Rot NUR auf KRITISCH — 4px-Bar als news-row__bar-Element (kein border-left).
 * K2: Kategorie- und Plattform-Chip auf jeder Zeile; TL;DR + Pillen inline auf KRITISCH.
 * K4: Checkbox nur wenn selectMode=true. Kein Stub im Normalzustand.
 * K6: read_by als Text; keine fetten 700er in NORMAL.
 */
import { useState } from "react"
import { platformLabel } from "../utils/platforms"
import { topicLabel }    from "../utils/topics"

function formatAge(iso) {
  if (!iso) return ""
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60)        return "gerade"
  if (diff < 3600)      return `${Math.floor(diff / 60)}m`
  if (diff < 86400)     return `${Math.floor(diff / 3600)}h`
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}d`
  return new Date(iso).toLocaleDateString("de-DE", { day: "2-digit", month: "short" })
}

// "anna.kraft@corp.de" -> "anna.k." | "akraft" -> "akraft"
function shortUser(user) {
  if (!user || user === "anonymous") return null
  const clean = user.replace(/@.*$/, "")
  const parts = clean.split(/[.\-_]/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0]}.${parts[1][0]}.`
  return clean.length > 12 ? clean.slice(0, 12) : clean
}

export default function NewsRow({
  article,
  isNew       = false,
  isRead      = false,
  readBy      = [],
  isFocused   = false,
  selected    = false,
  selectMode  = false,
  onMarkRead,
  onMarkUnread,
  onSelect,
  onSourceClick,
  onTopicClick,
}) {
  const [reasonOpen, setReasonOpen] = useState(false)

  const cat    = article.category || "NORMAL"
  const isKrit = cat === "KRITISCH"
  const plat   = article.platform ?? "cross"
  const topics = (article.topics || []).slice(0, 3)
  const haloUrl    = import.meta.env.VITE_HALO_TICKET_BASE_URL
  const ticketHref = haloUrl
    ? `${haloUrl}?summary=${encodeURIComponent(article.title)}&note=${encodeURIComponent(article.url ?? "")}`
    : null
  const readers = (readBy || []).filter(u => u && u !== "anonymous")

  const rowCls = [
    "news-row",
    isKrit    ? "news-row--kritisch" : "news-row--normal",
    isRead    ? "news-row--read"     : "",
    isFocused ? "news-row--focused"  : "",
    selected  ? "news-row--selected" : "",
  ].filter(Boolean).join(" ")

  function handleCopy(e) {
    e.stopPropagation()
    navigator.clipboard?.writeText(article.url ?? "").catch(() => {})
  }

  return (
    <div
      className={rowCls}
      data-id={article.id}
      onClick={onSelect}
      tabIndex={-1}
    >
      {/* K1: 4px Akzent-Balken — rot bei KRITISCH, transparent sonst */}
      <span className="news-row__bar" aria-hidden />

      {/* K4: Checkbox nur in selectMode */}
      {selectMode && (
        <span className={`news-row__sel${selected ? " --checked" : ""}`} aria-hidden />
      )}

      {/* Content */}
      <div className="news-row__body">

        {/* K2: Chip-Zeile */}
        <div className="news-row__chips">
          <span className={`cat-chip${isKrit ? " cat-chip--kritisch" : ""}`}>
            {isKrit ? "Kritisch" : "Normal"}
          </span>
          <span className={`plat-chip plat-chip--${plat}`}>
            {platformLabel(plat)}
          </span>
          {isNew && !isRead && <span className="new-chip">Neu</span>}
        </div>

        {/* Titel */}
        <a
          className="news-row__title"
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
        >
          {article.title}
        </a>

        {/* K2: TL;DR mit KI-Tag — nur KRITISCH, inline */}
        {isKrit && article.tldr && (
          <p className="news-row__tldr">
            <span className="ki-tag">KI</span>
            {"\u203A "}
            {article.tldr}
          </p>
        )}

        {/* K2: Meta-Pillen — nur KRITISCH */}
        {isKrit && (
          <div className="news-row__meta news-row__meta--badges">
            {(article.cve_ids ?? []).slice(0, 3).map(cve => (
              <span key={cve} className="badge--cve">{cve}</span>
            ))}
            {article.cvss != null && (
              <span className={`badge--cvss${article.cvss >= 9 ? " badge--cvss-high" : ""}`}>
                CVSS {Number(article.cvss).toFixed(1)}
              </span>
            )}
            {(article.cluster_size ?? 1) > 1 && (
              <span className="badge--cluster">
                {article.cluster_size} Quellen
              </span>
            )}
          </div>
        )}

        {/* Meta: Quelle · Topics · Alter · gelesen von */}
        <div className="news-row__meta">
          <button
            className="news-row__source"
            onClick={e => { e.stopPropagation(); onSourceClick?.(article.source) }}
            title={`Nur ${article.source} anzeigen`}
          >
            {article.source}
          </button>
          {topics.map(t => (
            <button
              key={t}
              className="topic-chip"
              onClick={e => { e.stopPropagation(); onTopicClick?.(t) }}
            >
              {topicLabel(t)}
            </button>
          ))}
          <span className="news-row__age">{formatAge(article.published_at)}</span>
          {readers.length > 0 && (
            <span className="news-row__readers">
              gelesen von{" "}
              {readers.slice(0, 2).map(shortUser).filter(Boolean).join(", ")}
              {readers.length > 2 && ` +${readers.length - 2}`}
            </span>
          )}
        </div>

        {/* classification_reason: aufklappbar, kein Stub wenn leer */}
        {article.classification_reason && (
          <div className="news-row__reason">
            <button
              className="reason-toggle"
              onClick={e => { e.stopPropagation(); setReasonOpen(o => !o) }}
              aria-expanded={reasonOpen}
            >
              {reasonOpen ? "Einblenden \u25b2" : "Warum? \u25bc"}
            </button>
            {reasonOpen && (
              <span className="reason-text">{article.classification_reason}</span>
            )}
          </div>
        )}
      </div>

      {/* Aktionen */}
      <div className="news-row__actions" onClick={e => e.stopPropagation()}>
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="action-btn"
          title="Öffnen (o)"
        >
          &#x2197;
        </a>
        {!isRead ? (
          <button
            className="action-btn"
            onClick={() => onMarkRead?.()}
            title="Als gelesen markieren (e)"
          >
            &#x2713;
          </button>
        ) : (
          <button
            className="action-btn action-btn--muted"
            onClick={() => onMarkUnread?.()}
            title="Als ungelesen markieren (u)"
          >
            &#x21BA;
          </button>
        )}
        <button
          className="action-btn action-btn--hover"
          onClick={handleCopy}
          title="Link kopieren"
        >
          &#x2398;
        </button>
        {ticketHref && (
          <a
            href={ticketHref}
            target="_blank"
            rel="noopener noreferrer"
            className="action-btn action-btn--hover"
            title="Ticket erstellen (t)"
          >
            T
          </a>
        )}
      </div>
    </div>
  )
}
