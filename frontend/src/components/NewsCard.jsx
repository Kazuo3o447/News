import { topicLabel } from '../utils/topics'

function formatDate(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  const now  = new Date()
  const diff = (now - date) / 1000
  if (diff < 60)        return 'gerade eben'
  if (diff < 3600)      return `vor ${Math.floor(diff / 60)} Min`
  if (diff < 86400)     return `vor ${Math.floor(diff / 3600)} Std`
  if (diff < 86400 * 7) return `vor ${Math.floor(diff / 86400)} Tg`
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: 'short', year: 'numeric' })
}

function stripHtml(html) {
  if (!html) return ''
  return html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
}

export default function NewsCard({ article }) {
  const cat      = (article.category || 'NORMAL').toLowerCase()
  const category = article.category || 'NORMAL'
  const summary  = stripHtml(article.summary)
  const topics   = article._topics || []

  return (
    <article className={`news-card news-card--${cat}`}>
      <div className="news-card__head">
        <span className={`badge badge--${cat}`}>
          <span className="badge__dot" />
          {category}
        </span>
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

      <div className="news-card__foot">
        <span>{formatDate(article.published_at)}</span>
        {article.confidence > 0 && (
          <span className="news-card__confidence" title="KI-Klassifizierungs-Konfidenz">
            ✨ {Math.round(article.confidence * 100)} %
          </span>
        )}
      </div>
    </article>
  )
}
