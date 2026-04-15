import { ref, computed } from 'vue'
import {
  listTranslations,
  getTranslation,
  updateTranslationName,
  deleteTranslation
} from '../api/translations'
import type { Translation, TranslationListParams, TranslationStatus } from '../types/translation'

export function useTranslations() {
  const translations = ref<Translation[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Filter state
  const statusFilter = ref<TranslationStatus | null>(null)
  const sourceLangFilter = ref<string | null>(null)
  const targetLangFilter = ref<string | null>(null)

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  async function list(params?: TranslationListParams): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const queryParams: TranslationListParams = {
        page: params?.page ?? currentPage.value,
        limit: params?.limit ?? pageSize.value,
        ...buildFilterParams()
      }
      // Override with explicit params if provided
      if (params?.status !== undefined) queryParams.status = params.status
      if (params?.source_lang !== undefined) queryParams.source_lang = params.source_lang
      if (params?.target_lang !== undefined) queryParams.target_lang = params.target_lang

      const result = await listTranslations(queryParams)
      translations.value = result.translations
      total.value = result.total
      currentPage.value = result.page
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load translations'
    } finally {
      loading.value = false
    }
  }

  function buildFilterParams(): Partial<TranslationListParams> {
    const params: Partial<TranslationListParams> = {}
    if (statusFilter.value) params.status = statusFilter.value
    if (sourceLangFilter.value) params.source_lang = sourceLangFilter.value
    if (targetLangFilter.value) params.target_lang = targetLangFilter.value
    return params
  }

  async function get(id: string): Promise<Translation | null> {
    loading.value = true
    error.value = null
    try {
      return await getTranslation(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to get translation'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateName(id: string, name: string): Promise<Translation | null> {
    loading.value = true
    error.value = null
    try {
      const updated = await updateTranslationName(id, name)
      // Update local list if present
      const idx = translations.value.findIndex(t => t.id === id)
      if (idx >= 0) {
        translations.value = [
          ...translations.value.slice(0, idx),
          updated,
          ...translations.value.slice(idx + 1)
        ]
      }
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update translation name'
      return null
    } finally {
      loading.value = false
    }
  }

  async function remove(id: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await deleteTranslation(id)
      // Optimistic update: remove from local list
      translations.value = translations.value.filter(t => t.id !== id)
      total.value = Math.max(0, total.value - 1)
      // If current page is now empty and we're not on page 1, go back
      if (translations.value.length === 0 && currentPage.value > 1) {
        currentPage.value -= 1
        await list()
      }
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete translation'
      return false
    } finally {
      loading.value = false
    }
  }

  function setPage(page: number): void {
    currentPage.value = page
    list()
  }

  function setPageSize(size: number): void {
    pageSize.value = size
    currentPage.value = 1
    list()
  }

  function setStatusFilter(status: TranslationStatus | null): void {
    statusFilter.value = status
    currentPage.value = 1
    list()
  }

  function setSourceLangFilter(lang: string | null): void {
    sourceLangFilter.value = lang
    currentPage.value = 1
    list()
  }

  function setTargetLangFilter(lang: string | null): void {
    targetLangFilter.value = lang
    currentPage.value = 1
    list()
  }

  function clearFilters(): void {
    statusFilter.value = null
    sourceLangFilter.value = null
    targetLangFilter.value = null
    currentPage.value = 1
    list()
  }

  function updateLocal(id: string, patch: Partial<Translation>): void {
    const idx = translations.value.findIndex(t => t.id === id)
    if (idx >= 0) {
      translations.value = [
        ...translations.value.slice(0, idx),
        { ...translations.value[idx], ...patch },
        ...translations.value.slice(idx + 1)
      ]
    }
  }

  return {
    // State
    translations,
    total,
    currentPage,
    pageSize,
    totalPages,
    loading,
    error,
    // Filter state
    statusFilter,
    sourceLangFilter,
    targetLangFilter,
    // Methods
    list,
    get,
    updateName,
    remove,
    setPage,
    setPageSize,
    setStatusFilter,
    setSourceLangFilter,
    setTargetLangFilter,
    clearFilters,
    updateLocal
  }
}
