import { ref, computed } from 'vue'
import { fetchMeetings } from '../api/meetings'
import type { MeetingListItem } from '../types'

export function useMeetings() {
  const meetings = ref<MeetingListItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const searchQuery = ref('')
  const activeFilter = ref<{ type: 'category' | 'tag'; value: string } | null>(null)
  const isLoading = ref(false)
  const serverError = ref(false)

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  let searchTimer: ReturnType<typeof setTimeout>

  async function load() {
    isLoading.value = true
    try {
      const params: Record<string, string | number> = {
        page: page.value,
        limit: pageSize.value,
      }
      if (searchQuery.value.trim()) params.q = searchQuery.value.trim()
      if (activeFilter.value?.type === 'category') params.category_id = activeFilter.value.value
      if (activeFilter.value?.type === 'tag')      params.tag = activeFilter.value.value

      const result = await fetchMeetings(params)
      meetings.value = result.meetings
      total.value = result.total
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
    searchTimer = setTimeout(() => {
      page.value = 1
      load()
    }, 300)
  }

  function setFilter(type: 'category' | 'tag', value: string) {
    if (activeFilter.value?.type === type && activeFilter.value?.value === value) {
      activeFilter.value = null
    } else {
      activeFilter.value = { type, value }
    }
    page.value = 1
    load()
  }

  function clearFilter() {
    activeFilter.value = null
    page.value = 1
    load()
  }

  function setPage(p: number) {
    page.value = p
    load()
  }

  function setPageSize(size: number) {
    pageSize.value = size
    page.value = 1
    load()
  }

  async function remove(id: string) {
    // Optimistic: remove locally, then reload to get correct total
    meetings.value = meetings.value.filter(m => m.id !== id)
    total.value = Math.max(0, total.value - 1)
    // If current page is now empty and we're not on page 1, go back
    if (meetings.value.length === 0 && page.value > 1) {
      page.value -= 1
    }
    await load()
  }

  function updateLocal(id: string, patch: Partial<MeetingListItem>) {
    const idx = meetings.value.findIndex(m => m.id === id)
    if (idx >= 0) meetings.value[idx] = { ...meetings.value[idx], ...patch }
  }

  return {
    meetings,
    total,
    page,
    pageSize,
    totalPages,
    searchQuery,
    activeFilter,
    isLoading,
    serverError,
    load,
    search,
    setFilter,
    clearFilter,
    setPage,
    setPageSize,
    remove,
    updateLocal,
  }
}
