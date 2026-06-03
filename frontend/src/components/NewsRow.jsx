/**
 * F5 — NewsRow: kompakte Listenzeile für NORMAL/übrige Artikel.
 * Props analog NewsCard.
 */

const PLAT_ICON  = { windows: '🪟', apple: '', android: '', cross: '⛓' }
const PLAT_LABEL = { windows: 'Windows', apple: 'Apple', android: 'Android', cross: 'Cross' }

function formatDate(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  const now  = new Date()
  const diff = (now - date) / 1000
  if (diff < 60)        return 'gerade'
  if (diff < 3600)      return `${Math.floor(diff / 60)}m`
  if (diff < 86400)     return `${Math.floor(diff / 3600)}h`
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}d`
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: 'short' })
}

export default function NewsRow({ article, isNew = false, isRead = false, onMarkRead }) {
  const cat      = (article.category || 'NORMAL').toLowerCase()
  const platform = article.platform ?? 'cross'

  const haloUrl     = import.meta.env.VITE_HALO_TICKET_BASE_URL
  const ticketHref  = haloUrl
    ? `${haloUrl}?summary=${encodeURIComponent(article.title)}&note=${encodeURIComponent(article.url)}`
    : null

  function handleCopy(e) {
    e.preventDefault()
    navigator.clipboard?.writeText(article.url).catch(() => {})
  }

  const rowClass = [
    'news-row',
    cat === 'dump'      ? 'news-row--dump'      : '',
    cat === 'off_topic' ? 'news-row--dump'      : '',
    isRead              ? 'news-row--read'      : '',
  ].filter(Boolean).join(' ')

  return (
    <div className={rowClass}>
      <div className="news-row__badges">
        <span
          className={`badge--platform badge--${platform}`}
          title={PLAT_LABEL[platform] ?? platform}
        >
          {PLAT_ICON[platform] ?? '🌐'}
        </span>
        {isNew && <span className="dot--new" title="Neu seit letztem Besuch" />}
      </div>

      <div className="news-row__title" title={article.classification_reason || ''}>
        <a href={article.url} target="_blank" rel="noopener noreferrer">
          {article.title}
        </a>
      </div>

      <span className="news-row__source">{article.source}</span>

      <span className="news-row__time">{formatDate(article.published_at)}</span>

      <div className="news-row__actions">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="action-btn action-btn--icon"
          title="Öffnen"
        >
          ↗
        </a>
        {!isRead && (
          <button
            className="action-btn action-btn--icon"
            onClick={() => onMarkRead?.(article.id)}
            title="Als gelesen markieren"
          >
            ✓
          </button>
        )}
        <button
          className="action-btn action-btn--icon"
          onClick={handleCopy}
          title="Link kopieren"
        >
          📋
        </button>
        {ticketHref && (
          <a
            href={ticketHref}
            target="_blank"
            rel="noopener noreferrer"
            className="action-btn action-btn--icon"
            title="Ticket erstellen"
          >
            🎫
          </a>
        )}
      </div>
    </div>
  )
}
