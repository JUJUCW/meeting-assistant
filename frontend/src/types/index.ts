export interface Category {
  id: string
  name: string
}

export interface Decision {
  id: string
  content: string
  rationale: string
  related_people: string[]
  status: 'confirmed' | 'pending' | 'cancelled'
}

export interface ActionItem {
  id: string
  content: string
  assignee: string
  deadline: string | null
  priority: 'low' | 'medium' | 'high'
  status: 'pending' | 'done'
}

export interface SearchHit {
  field: 'transcript' | 'decisions' | 'action_items'
  snippet: string
}

export interface MeetingListItem {
  id: string
  created_at: string
  title?: string
  tags: string[]
  category_id?: string
  decision_count: number
  action_item_count: number
  pending_action_item_count: number
  hits?: SearchHit[]
}

export interface PaginatedMeetings {
  meetings: MeetingListItem[]
  total: number
  page: number
  limit: number
}

export interface Meeting extends MeetingListItem {
  transcript: string
  summary?: string
  decisions: Decision[]
  action_items: ActionItem[]
  date?: string
}

export interface TranscriptionStatus {
  status: 'pending' | 'processing' | 'done' | 'error'
  message?: string
}

export interface TranscriptionResult {
  meeting_id: string
  transcript: string
  segments: Array<{ start: number; end: number; text: string }>
  decisions: Decision[]
  action_items: ActionItem[]
  resolved_item_ids: string[]
  ollama_available: boolean
}
