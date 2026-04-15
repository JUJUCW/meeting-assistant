/**
 * Translations API client
 * Matches backend REST endpoints from design.md section 3.1.3
 */

import { api } from './client'
import type {
  Translation,
  PaginatedTranslations,
  StartTranslationResponse,
} from '../types/translation'

export interface TranslationFilters {
  page?: number
  limit?: number
  status?: string
  source_lang?: string
  target_lang?: string
  q?: string
}

/**
 * Start a new translation session
 * POST /api/translations/start
 * @throws Error with detail if 409 Conflict (existing in_progress session)
 */
export const startTranslation = (): Promise<StartTranslationResponse> =>
  api.post<StartTranslationResponse>('/api/translations/start', {})

/**
 * List translation sessions with optional filters
 * GET /api/translations
 */
export const listTranslations = (
  filters: TranslationFilters = {}
): Promise<PaginatedTranslations> => {
  const params = new URLSearchParams()
  if (filters.page) params.set('page', String(filters.page))
  if (filters.limit) params.set('limit', String(filters.limit))
  if (filters.status) params.set('status', filters.status)
  if (filters.source_lang) params.set('source_lang', filters.source_lang)
  if (filters.target_lang) params.set('target_lang', filters.target_lang)
  if (filters.q) params.set('q', filters.q)
  const query = params.toString()
  return api.get<PaginatedTranslations>(
    `/api/translations${query ? `?${query}` : ''}`
  )
}

/**
 * Get a single translation session with all sentences
 * GET /api/translations/{id}
 */
export const getTranslation = (id: string): Promise<Translation> =>
  api.get<Translation>(`/api/translations/${encodeURIComponent(id)}`)

/**
 * Update translation session name
 * PATCH /api/translations/{id}
 */
export const updateTranslationName = (
  id: string,
  name: string
): Promise<Translation> =>
  api.patch<Translation>(`/api/translations/${encodeURIComponent(id)}`, { name })

/**
 * Delete a translation session and its audio file
 * DELETE /api/translations/{id}
 */
export const deleteTranslation = (id: string): Promise<void> =>
  api.del<void>(`/api/translations/${encodeURIComponent(id)}`)

/**
 * Get audio download URL for a translation session
 * Returns the URL path (not a fetch call)
 */
export const getAudioUrl = (id: string): string =>
  `/api/translations/${encodeURIComponent(id)}/audio`

/**
 * Get DOCX export URL for a translation session
 * Returns the URL path (not a fetch call)
 */
export const getExportUrl = (id: string): string =>
  `/api/translations/${encodeURIComponent(id)}/export/docx`

/**
 * Build WebSocket URL for live translation stream
 * Returns the full WebSocket URL
 */
export const getStreamUrl = (id: string): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/api/translations/${encodeURIComponent(id)}/stream`
}
