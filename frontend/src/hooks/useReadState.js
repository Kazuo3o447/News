/**
 * F4 — useReadState: Team-Read-State über Backend-API (Brief 03 B2).
 * Optimistisches Update: UI sofort, dann Server-Call im Hintergrund.
 * localStorage nur noch für UI-Vorlieben (platform, view, lastVisitAt, darkMode).
 */
import { useCallback, useRef, useState } from "react"
import axios from "axios"

const API = {
  markRead:   (id)  => axios.post(`/api/articles/${id}/read`).catch(() => {}),
  markUnread: (id)  => axios.delete(`/api/articles/${id}/read`).catch(() => {}),
  markBulk:   (ids) => axios.post("/api/articles/read/bulk", { ids }).catch(() => {}),
}

/**
 * Returns:
 *   readMap   : Record<articleId, string[]>  — read_by lists from server response
 *   localRead : Set<string>                  — optimistic local additions
 *   markRead, markUnread, markBulk
 *   isRead(id, currentUser)
 *   initReadMap(items)                       — seed from API response
 */
export function useReadState(currentUser = "anonymous") {
  // server-delivered read_by map, keyed by article id
  const [readMap, setReadMap] = useState({})
  // optimistic local reads (not yet confirmed by server)
  const localRead = useRef(new Set())

  /** Seed read_by from an API response batch */
  const initReadMap = useCallback((items) => {
    const map = {}
    for (const item of items) {
      if (item.id != null) {
        map[item.id] = item.read_by ?? []
      }
    }
    setReadMap(map)
  }, [])

  const isRead = useCallback((id) => {
    if (localRead.current.has(id)) return true
    const readers = readMap[id] ?? []
    return readers.includes(currentUser)
  }, [readMap, currentUser])

  const markRead = useCallback((id) => {
    localRead.current.add(id)
    // Update readMap to include currentUser optimistically
    setReadMap(prev => {
      const existing = prev[id] ?? []
      if (existing.includes(currentUser)) return prev
      return { ...prev, [id]: [...existing, currentUser] }
    })
    API.markRead(id)
  }, [currentUser])

  const markUnread = useCallback((id) => {
    localRead.current.delete(id)
    setReadMap(prev => ({
      ...prev,
      [id]: (prev[id] ?? []).filter(u => u !== currentUser),
    }))
    API.markUnread(id)
  }, [currentUser])

  const markBulk = useCallback((ids) => {
    for (const id of ids) localRead.current.add(id)
    setReadMap(prev => {
      const next = { ...prev }
      for (const id of ids) {
        const existing = next[id] ?? []
        if (!existing.includes(currentUser)) {
          next[id] = [...existing, currentUser]
        }
      }
      return next
    })
    API.markBulk(ids)
  }, [currentUser])

  return { readMap, isRead, markRead, markUnread, markBulk, initReadMap }
}
