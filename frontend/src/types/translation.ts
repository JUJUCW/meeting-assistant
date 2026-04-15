/**
 * Translation feature types
 * Matches backend API contracts from design.md section 3.2
 */

export type TranslationStatus = 'in_progress' | 'completed' | 'interrupted'

export interface Sentence {
  sentence_id: string
  sequence: number
  offset_sec: number
  original_text: string
  translated_text: string
  confidence: number
}

export interface Translation {
  id: string
  name: string
  started_at: string
  ended_at: string | null
  duration_sec: number
  source_lang: string
  target_lang: string
  status: TranslationStatus
  audio_path: string | null
  audio_size_bytes: number | null
  sentences: Sentence[]
}

export interface TranslationListItem {
  id: string
  name: string
  started_at: string
  duration_sec: number
  source_lang: string
  target_lang: string
  sentence_count: number
  status: TranslationStatus
}

export interface PaginatedTranslations {
  translations: TranslationListItem[]
  total: number
  page: number
  limit: number
}

/**
 * WebSocket message types for live translation stream
 */
export type LiveTranslateMessageType = 'sentence' | 'translation' | 'status' | 'error'

export interface SentenceMessage {
  type: 'sentence'
  data: Sentence
}

export interface TranslationMessage {
  type: 'translation'
  sentence_id: string
  translated_text: string
}

export interface StatusMessage {
  type: 'status'
  status: 'completed' | 'interrupted'
}

export interface ErrorMessage {
  type: 'error'
  message: string
}

export type LiveTranslateServerMessage =
  | SentenceMessage
  | TranslationMessage
  | StatusMessage
  | ErrorMessage

// Alias for backward compatibility
export type WSMessage = LiveTranslateServerMessage

/**
 * Client-to-server message types
 */
export interface StopMessage {
  type: 'stop'
}

export type LiveTranslateClientMessage = StopMessage

/**
 * API response types
 */
export interface StartTranslationResponse {
  id: string
}

export interface ConflictResponse {
  detail: string
  existing_id: string
}

/**
 * Query parameters for listing translations
 */
export interface TranslationListParams {
  page?: number
  limit?: number
  status?: TranslationStatus
  source_lang?: string
  target_lang?: string
  q?: string
}
