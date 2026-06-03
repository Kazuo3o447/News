import { topicLabel } from "../utils/topics"

function formatDate(iso) {
  if (!iso) return ""
  const date = new Date(iso)
  const now  = new Date()
  const diff = (now - date) / 1000
  if (diff < 60)        return "gerade eben"
  if (diff < 3600)      return `vor ${Math.floor(diff / 60)} Min`
  if (diff < 86400)     return `vor ${Math.floor(diff / 3600)} Std`
  if (diff < 86400 * 7) return `vor ${Math.floor(diff / 86400)} Tg`
  return date.toLocaleDateString("de-DE", { day: "2-digit", month: "short", year: "numeric" })
}

function stripHtml(html) {
  if (!html) return ""
  return html.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim()
}

const PLAT_ICON  = { windows: "🪟", apple: "", android: "", cross: "⛓" }
const PLAT_LABEL = { windows: "Windows", apple: "Apple", android: "Android", cross: "Cross" }

function PlatformBadge({ platform }) {
  if (!platform) return null
  return (
    <span className={`badge--platform badge--${platform}`} title={PLAT_LABEL[platform] ?? platform}>
      {PLAT_ICON[platform] ?? "🌐"} {PLAT_LABEL[platform] ?? platform}
    </span>
  )
}

function CategoryLabel(cat) {
  if (cat === "DUMP") return "Aussortiert"
  if (cat === "OFF_TOPIC") return "Off-Topic"
  return cat
}

export default function NewsCard({ article, isNew = false, isRead = false, onMarkRead }) {
  const cat      = (article.category || "NORMAL").toLowerCase()
  const category = article.category || "NORMAL"
  const summary  = stripHtml(article.summary)
  const topics   = article._topics || []

  const haloUrl  = import.meta.env.VITE_HALO_TICKET_BASE_URL
  const ticketHref = haloUrl
    ? `${haloUrl}?summary=${encodeURIComponent(article.title)}&note=${encodeURIComponent(article.url)}`
    : null

  function handleCopy(e) {
    e.preventDefault()
    navigator.clipboard?.writeText(article.url).catch(() => {})
  }

  return (
    <article className={`news-card news-card--${cat}${isRead ? " news-card--read" : ""}`}>
      <div className="news-card__head">
        <span
          className={`badge badge--${cat}`}
          title={article.classification_reason || ""}
        >
          <span className="badge__dot" />
          {CategoryLabel(category)}
        </span>
        <PlatformBadge platform={article.platform ?? "cross"} />
        {isNew && <span className="badge--new"><span className="dot--new" />Neu</span>}
        <span className="news-card__source">{article.source}</span>
      </div>

      <h3 className="news-card__title">
        <a href={article.url} target="_blank" rel="noopener noreferrer">
          {article.title}
        </a>
      </h3>

      {summary && <p className="news-card__summary">{summary}</p>}

      {topics.length > 0 && (
        <div className="news-card__topics">
          {topics.slice(0, 4).map(t => (
            <span key={t} className={`topic-tag topic-tag--${t}`}>
              {topicLabel(t)}
            </span>
          ))}
        </div>
      )}

      <div className="news-card__actions">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="action-btn"
        >
          Öffnen ↗
        </a>
        {!isRead && (
          <button className="action-btn" onClick={() => onMarkRead?.(article.id)}>
            Gelesen ✓
          </button>
        )}
        <button className="action-btn action-btn--icon" onClick={handleCopy} title="Link kopieren">
          📋
        </button>
        {ticketHref && (
          <a
            href={ticketHref}
            target="_blank"
            rel="noopener noreferrer"
            className="action-btn"
          >
            Ticket erstellen
          </a>
        )}
      </div>

      <div className="news-card__foot">
        <span>{formatDate(article.published_at)}</span>
      </div>
    </article>
  )
}
