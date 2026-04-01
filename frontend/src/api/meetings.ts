import { api } from './client'
import type { Meeting, MeetingListItem, Decision, ActionItem } from '../types'

export const fetchMeetings = () =>
  api.get<{ meetings: MeetingListItem[] }>('/meetings').then(r => r.meetings)

export const searchMeetings = (q: string) =>
  api.get<{ meetings: MeetingListItem[] }>(`/meetings/search?q=${encodeURIComponent(q)}`).then(r => r.meetings)

export const getMeeting = (id: string) =>
  api.get<Meeting>(`/meetings/${encodeURIComponent(id)}`)

export const deleteMeeting = (id: string) =>
  api.del<void>(`/meetings/${encodeURIComponent(id)}`)

export const patchMeetingTitle = (id: string, title: string) =>
  api.patch<Meeting>(`/meetings/${encodeURIComponent(id)}/title`, { title })

export const patchMeetingTags = (id: string, body: { category_id?: string; tags?: string[] }) =>
  api.patch<Meeting>(`/meetings/${encodeURIComponent(id)}/tags`, body)

export const createDecision = (meetingId: string, body: Partial<Decision>) =>
  api.post<Decision>(`/meetings/${encodeURIComponent(meetingId)}/decisions`, body)

export const patchDecision = (meetingId: string, decisionId: string, body: Partial<Decision>) =>
  api.patch<Decision>(`/meetings/${encodeURIComponent(meetingId)}/decisions/${decisionId}`, body)

export const createActionItem = (meetingId: string, body: Partial<ActionItem>) =>
  api.post<ActionItem>(`/meetings/${encodeURIComponent(meetingId)}/action-items`, body)

export const patchActionItem = (meetingId: string, itemId: string, body: Partial<ActionItem>) =>
  api.patch<ActionItem>(`/meetings/${encodeURIComponent(meetingId)}/action-items/${itemId}`, body)

export const postGenerateSummary = (id: string) =>
  api.post<{ summary: string }>(`/meetings/${encodeURIComponent(id)}/summary`, {})

export const getMeetingDocxUrl = (id: string) =>
  `/meetings/${encodeURIComponent(id)}/export/docx`

export const getPendingActionItems = () =>
  api.get<ActionItem[]>('/action-items/pending')

export const resolveActionItem = (meetingId: string, itemId: string) =>
  api.post<ActionItem>(`/action-items/${encodeURIComponent(meetingId)}/${itemId}/resolve`, {})
