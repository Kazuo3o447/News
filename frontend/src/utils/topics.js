/**
 * Client-seitige Topic-Erkennung anhand Keywords in Titel + Summary.
 * Liefert eine Liste von Topic-Keys pro Artikel.
 */

export const TOPICS = [
  { key: 'security',  label: 'Security',           keywords: ['security', 'sicherheits', 'cve', 'vulnerab', 'exploit', 'patch', 'malware', 'ransomware', 'phishing', 'breach', 'leak', 'angriff', 'hack', 'zero-day', 'zero day', 'cyber', 'krebs', 'bsi'] },
  { key: 'microsoft', label: 'Microsoft / Azure',  keywords: ['microsoft', 'azure', 'windows', 'office 365', 'microsoft 365', 'm365', 'teams', 'sharepoint', 'outlook', 'exchange', 'entra', 'copilot', 'edge', 'surface', 'visual studio', 'dotnet', '.net'] },
  { key: 'ai',        label: 'AI / KI',            keywords: ['ai ', ' ai', 'a.i.', 'künstliche intelligenz', 'kuenstliche intelligenz', ' ki ', 'chatgpt', 'gpt-', 'llm', 'gemini', 'claude', 'anthropic', 'openai', 'mistral', 'deepseek', 'copilot', 'machine learning', 'neural', 'sprachmodell'] },
  { key: 'cloud',     label: 'Cloud / DevOps',     keywords: ['cloud', 'aws', 'amazon web services', 'gcp', 'google cloud', 'kubernetes', 'docker', 'container', 'serverless', 'devops', 'ci/cd', 'terraform', 'iac'] },
  { key: 'dev',       label: 'Entwicklung',        keywords: ['javascript', 'typescript', 'python', 'java ', 'rust', 'golang', ' go ', 'react', 'vue', 'angular', 'node.js', 'npm ', 'framework', 'api ', 'rest', 'graphql', 'git', 'github', 'gitlab', 'visual studio code', 'vscode', 'open source', 'open-source'] },
  { key: 'hardware',  label: 'Hardware / Chips',   keywords: ['cpu', 'gpu', 'chip', 'prozessor', 'intel', 'amd', ' arm ', 'nvidia', 'rtx', 'ryzen', 'core ultra', 'snapdragon', 'apple silicon', 'laptop', 'notebook', 'pc ', ' pc', 'mainboard', 'ssd', 'arbeitsspeicher', 'ram '] },
  { key: 'mobile',    label: 'Mobile',             keywords: ['iphone', 'ipad', 'ios ', 'android', 'samsung', 'google pixel', 'smartphone', 'tablet', '5g', '6g'] },
]

/** Erkennt Topics aus Titel + Summary. */
export function detectTopics(article) {
  const text = `${article.title || ''} ${article.summary || ''}`.toLowerCase()
  const found = []
  for (const topic of TOPICS) {
    if (topic.keywords.some(kw => text.includes(kw))) {
      found.push(topic.key)
    }
  }
  return found
}

/** Label-Lookup für einen Topic-Key. */
export function topicLabel(key) {
  return TOPICS.find(t => t.key === key)?.label ?? key
}
