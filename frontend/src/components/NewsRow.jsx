/**
 * F2 â€” NewsRow: einheitliche Listenzeile fÃ¼r KRITISCH und NORMAL.
 *
 * KRITISCH: roter Balken links, TL;DR-Zeile sichtbar, CVE/CVSS-Badges, Cluster-ZÃ¤hler.
 * NORMAL:   kompakte ~44px-Zeile, eine Zeile.
 * Gelesene Zeilen: ausgegraut.
 * Fokus-Ring in GEMA-Rot (Tastatur-Navigation F3).
 *
 * Props:
 *   article        â€“ Artikel-Objekt (inkl. is_priority, tldr, cve_ids, cvss, cluster_size, read_by)
 *   isNew          â€“ Bool: wurde nach letztem Besuch verÃ¶ffentlicht?
 *   isRead         â€“ Bool: vom aktuellen User gelesen?
 *   readBy         â€“ string[]: andere User die gelesen haben
 *   isFocused      â€“ Bool: tastatur-fokussiert (F3)
 *   selected       â€“ Bool: per Shift-Klick ausgewÃ¤hlt (F3 Bulk)
 *   onMarkRead     â€“ () => void
 *   onMarkUnread   â€“ () => void
 *   onSelect       â€“ (e: MouseEvent) => void (Shift-Klick)
 *   onSourceClick  â€“ (source: string) => void
 *   onTopicClick   â€“ (topic: string) => void
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

function initials(user) {
  if (!user || user === "anonymous") return null
  const parts = user.split(/[.\s@]/).filter(Boolean)
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : user.slice(0, 2).toUpperCase()
}

export default function NewsRow({
  article,
  isNew       = false,
  isRead      = false,
  readBy      = [],
  isFocused   = false,
  selected    = false,
  onMarkRead,
  onMarkUnread,
  onSelect,
  onSourceClick,
  onTopicClick,
}) {
  const [reasonOpen, setReasonOpen] = useState(false)

  const cat     = article.category || "NORMAL"
  const isKrit  = cat === "KRITISCH"
  const plat    = article.platform ?? "cross"
  const topics  = (article.topics || []).slice(0, 3)
  const haloUrl = import.meta.env.VITE_HALO_TICKET_BASE_URL
  const ticketHref = haloUrl
    ? `${haloUrl}?summary=${encodeURIComponent(article.title)}&note=${encodeURIComponent(article.url ?? "")}`
    : null

  const others = readBy.filter(u => u && u !== "anonymous")

  const rowCls = [
    "news-row",
    isKrit                           ? "news-row--kritisch"  : "news-row--normal",
    isRead                           ? "news-row--read"       : "",
    isFocused                        ? "news-row--focused"    : "",
    selected                         ? "news-row--selected"   : "",
    article.is_priority && !isKrit   ? "news-row--priority"   : "",
  ].filter(Boolean).join(" ")

  function handleCopy(e) {
    e.preventDefault()
    navigator.clipboard?.writeText(article.url ?? "").catch(() => {})
  }

  return (
    <div
      className={rowCls}
      data-id={article.id}
      onClick={onSelect}
      tabIndex={-1}
    >
      {/* Selection indicator */}
      <span className={`news-row__sel${selected ? " --checked" : ""}`} aria-hidden />

      {/* Platform badge */}
      <span className={`badge--platform badge--${plat}`}>
        {platformLabel(plat)}
      </span>

      {/* New dot */}
      {isNew && !isRead && <span className="dot--new" title="Neu seit letztem Besuch" />}

      {/* Content column */}
      <div className="news-row__body">
        {/* Title */}
        <div className="news-row__title-row">
          <a
            className="news-row__title"
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
          >
            {article.title}
          </a>
        </div>

        {/* KRITISCH: TL;DR + badges */}
        {isKrit && (
          <>
            {article.tldr && (
              <p className="news-row__tldr">{article.tldr}</p>
            )}
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
          </>
        )}

        {/* Meta row */}
        <div className="news-row__meta">
          <button
            className="news-row__source"
            onClick={(e) => { e.stopPropagation(); onSourceClick?.(article.source) }}
            title={`Nur ${article.source} anzeigen`}
          >
            {article.source}
          </button>

          {!isKrit && topics.map(t => (
            <button
              key={t}
              className="topic-chip"
              onClick={(e) => { e.stopPropagation(); onTopicClick?.(t) }}
            >
              {topicLabel(t)}
            </button>
          ))}

          <span className="news-row__age">{formatAge(article.published_at)}</span>

          {/* Team read indicators */}
          {others.length > 0 && (
            <span className="news-row__readers" title={`Gelesen von: ${others.join(", ")}`}>
              {others.slice(0, 3).map(u => (
                <span key={u} className="avatar">{initials(u)}</span>
              ))}
              {others.length > 3 && (
                <span className="avatar avatar--more">+{others.length - 3}</span>
              )}
            </span>
          )}
        </div>

        {/* "Warum?" aufklappbar */}
        {article.classification_reason && (
          <div className="news-row__reason">
            <button
              className="reason-toggle"
              onClick={(e) => { e.stopPropagation(); setReasonOpen(o => !o) }}
              aria-expanded={reasonOpen}
            >
              {reasonOpen ? "Grund \u25b2" : "Grund \u25bc"}
            </button>
            {reasonOpen && (
              <span className="reason-text">{article.classification_reason}</span>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="news-row__actions" onClick={e => e.stopPropagation()}>
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="action-btn"
          title="Ã–ffnen (o)"
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
          className="action-btn action-btn--icon"
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
            className="action-btn"
            title="Ticket erstellen (t)"
          >
            T
          </a>
        )}
      </div>
    </div>
  )
}
