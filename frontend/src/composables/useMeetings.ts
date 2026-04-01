import { ref, computed } from 'vue'
import { fetchMeetings, searchMeetings, deleteMeeting } from '../api/meetings'
import type { MeetingListItem } from '../types'

export function useMeetings() {
  const allMeetings = ref<MeetingListItem[]>([])
  const searchQuery = ref('')
  const searchResults = ref<MeetingListItem[] | null>(null)
  const activeFilter = ref<{ type: 'category' | 'tag'; value: string } | null>(null)
  const isLoading = ref(false)
  const serverError = ref(false)

  let searchTimer: ReturnType<typeof setTimeout>

  const displayedMeetings = computed<MeetingListItem[]>(() => {
    const base = searchResults.value ?? allMeetings.value
    if (!activeFilter.value) return base
    const { type, value } = activeFilter.value
    if (type === 'category') return base.filter(m => m.category_id === value)
    if (type === 'tag')      return base.filter(m => (m.tags ?? []).includes(value))
    return base
  })

  async function load() {
    isLoading.value = true
    try {
      const meetings = await fetchMeetings()
      allMeetings.value = [...meetings].sort((a, b) =>
        (b.created_at ?? '').localeCompare(a.created_at ?? '')
      )
      serverError.value = false
    } catch {
      serverError.value = true
    } finally {
      isLoading.value = false
    }
  }

  function search(q: string) {
    searchQuery.value = q
    clearTimeout(searchTimer)
    if (!q.trim()) {
      searchResults.value = null
      return
    }
    searchTimer = setTimeout(async () => {
      try {
        searchResults.value = await searchMeetings(q)
      } catch {
        searchResults.value = []
      }
    }, 300)
  }

  function setFilter(type: 'category' | 'tag', value: string) {
    if (activeFilter.value?.type === type && activeFilter.value?.value === value) {
      activeFilter.value = null
    } else {
      activeFilter.value = { type, value }
    }
  }

  function clearFilter() {
    activeFilter.value = null
  }

  async function remove(id: string) {
    await deleteMeeting(id)
    allMeetings.value = allMeetings.value.filter(m => m.id !== id)
    if (searchResults.value) {
      searchResults.value = searchResults.value.filter(m => m.id !== id)
    }
  }

  function updateLocal(id: string, patch: Partial<MeetingListItem>) {
    const idx = allMeetings.value.findIndex(m => m.id === id)
    if (idx >= 0) allMeetings.value[idx] = { ...allMeetings.value[idx], ...patch }
    if (searchResults.value) {
      const si = searchResults.value.findIndex(m => m.id === id)
      if (si >= 0) searchResults.value[si] = { ...searchResults.value[si], ...patch }
    }
  }

  return {
    allMeetings,
    displayedMeetings,
    searchQuery,
    activeFilter,
    isLoading,
    serverError,
    load,
    search,
    setFilter,
    clearFilter,
    remove,
    updateLocal,
  }
}
