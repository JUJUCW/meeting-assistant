import { ref } from 'vue'
import {
  getMeeting,
  patchMeetingTitle,
  createDecision,
  patchDecision,
  createActionItem,
  patchActionItem,
} from '../api/meetings'
import type { Meeting, Decision, ActionItem } from '../types'

export function useMeetingDetail() {
  const meeting = ref<Meeting | null>(null)
  const isLoading = ref(false)
  const error = ref('')

  async function load(id: string) {
    isLoading.value = true
    error.value = ''
    try {
      meeting.value = await getMeeting(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      isLoading.value = false
    }
  }

  async function updateTitle(title: string) {
    if (!meeting.value) return
    await patchMeetingTitle(meeting.value.id, title)
    meeting.value = { ...meeting.value, title }
  }

  async function addDecision(body: Partial<Decision>): Promise<Decision> {
    if (!meeting.value) throw new Error('no meeting')
    const d = await createDecision(meeting.value.id, body)
    meeting.value = { ...meeting.value, decisions: [...(meeting.value.decisions ?? []), d] }
    return d
  }

  async function updateDecision(decisionId: string, body: Partial<Decision>) {
    if (!meeting.value) return
    const updated = await patchDecision(meeting.value.id, decisionId, body)
    meeting.value = {
      ...meeting.value,
      decisions: meeting.value.decisions.map(d => String(d.id) === String(decisionId) ? updated : d),
    }
  }

  async function addAction(body: Partial<ActionItem>): Promise<ActionItem> {
    if (!meeting.value) throw new Error('no meeting')
    const a = await createActionItem(meeting.value.id, body)
    meeting.value = { ...meeting.value, action_items: [...(meeting.value.action_items ?? []), a] }
    return a
  }

  async function updateAction(itemId: string, body: Partial<ActionItem>) {
    if (!meeting.value) return
    const updated = await patchActionItem(meeting.value.id, itemId, body)
    meeting.value = {
      ...meeting.value,
      action_items: meeting.value.action_items.map(a => String(a.id) === String(itemId) ? updated : a),
    }
  }

  async function toggleActionStatus(itemId: string) {
    if (!meeting.value) return
    const a = meeting.value.action_items.find(x => String(x.id) === String(itemId))
    if (!a) return
    const newStatus = a.status === 'done' ? 'pending' : 'done'
    await updateAction(itemId, { status: newStatus })
  }

  function close() {
    meeting.value = null
    error.value = ''
  }

  return { meeting, isLoading, error, load, close, updateTitle, addDecision, updateDecision, addAction, updateAction, toggleActionStatus }
}
