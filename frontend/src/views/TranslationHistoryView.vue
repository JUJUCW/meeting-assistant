<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import Pagination from '../components/history/Pagination.vue'
import TranslationCard from '../components/translation/TranslationCard.vue'
import { useTranslations } from '../composables/useTranslations'
import type { TranslationStatus, TranslationListItem } from '../types/translation'

const router = useRouter()
const {
  translations,
  total,
  currentPage,
  pageSize,
  totalPages,
  loading,
  error,
  statusFilter,
  list,
  remove,
  setPage,
  setPageSize,
  setStatusFilter,
  clearFilters
} = useTranslations()

const searchQuery = ref('')

const hasActiveFilter = computed(() =>
  statusFilter.value !== null || searchQuery.value.trim() !== ''
)

// translations is already TranslationListItem[] from the composable
const translationItems = computed<TranslationListItem[]>(() => translations.value)

onMounted(() => {
  list()
})

function openDetail(id: string): void {
  router.push(`/translation/${id}`)
}

async function onDeleted(id: string): Promise<void> {
  await remove(id)
}

function onStatusFilter(status: TranslationStatus | null): void {
  setStatusFilter(status)
}

function onSearch(): void {
  // Trigger reload with search query
  list({ q: searchQuery.value.trim() || undefined })
}

function onClearFilters(): void {
  searchQuery.value = ''
  clearFilters()
}

function goToLiveTranslate(): void {
  router.push('/live-translate')
}
</script>

<template>
  <div>
    <AppHeader
      eyebrow="History"
      title="翻譯歷史"
      subtitle="Translation History"
      :show-back="true"
      back-to="/"
      back-label="← 返回首頁"
    />

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜尋名稱..."
          class="search-input"
          @keyup.enter="onSearch"
        />
        <button class="btn-search" @click="onSearch">搜尋</button>
      </div>

      <div class="filter-group">
        <button
          class="filter-btn"
          :class="{ active: statusFilter === null }"
          @click="onStatusFilter(null)"
        >全部</button>
        <button
          class="filter-btn"
          :class="{ active: statusFilter === 'in_progress' }"
          @click="onStatusFilter('in_progress')"
        >錄音中</button>
        <button
          class="filter-btn"
          :class="{ active: statusFilter === 'completed' }"
          @click="onStatusFilter('completed')"
        >已完成</button>
        <button
          class="filter-btn"
          :class="{ active: statusFilter === 'interrupted' }"
          @click="onStatusFilter('interrupted')"
        >已中斷</button>
      </div>

      <div class="page-size-selector">
        <span class="page-size-label">每頁</span>
        <button
          v-for="n in [8, 20, 50]"
          :key="n"
          class="page-size-btn"
          :class="{ active: pageSize === n }"
          @click="setPageSize(n)"
        >{{ n }}</button>
      </div>
    </div>

    <!-- Active filter bar -->
    <div v-if="hasActiveFilter" class="filter-bar">
      <span class="filter-label">
        篩選中
        <template v-if="statusFilter">：{{ statusFilter }}</template>
        <template v-if="searchQuery.trim()">，關鍵字「{{ searchQuery }}」</template>
      </span>
      <button class="filter-clear" @click="onClearFilters">✕ 清除篩選</button>
    </div>

    <!-- Error message -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      載入中...
    </div>

    <!-- Translation list -->
    <div v-else-if="translationItems.length > 0" class="translation-list">
      <TranslationCard
        v-for="t in translationItems"
        :key="t.id"
        :translation="t"
        @open="openDetail"
        @deleted="onDeleted"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <p class="empty-text">尚無翻譯紀錄</p>
      <button class="btn-start" @click="goToLiveTranslate">
        開始即時翻譯 →
      </button>
    </div>

    <!-- Pagination -->
    <Pagination
      v-if="total > 0"
      :page="currentPage"
      :total-pages="totalPages"
      :total="total"
      :page-size="pageSize"
      @update:page="setPage"
    />
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  gap: 8px;
  flex: 1;
  min-width: 200px;
  max-width: 400px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--gold-dim);
  color: var(--cream);
  font-size: 13px;
  letter-spacing: 0.04em;
  outline: none;
  transition: border-color 0.2s;
}
.search-input:focus {
  border-color: var(--gold);
}
.search-input::placeholder {
  color: var(--muted);
}

.btn-search {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--gold-dim);
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-search:hover {
  border-color: var(--gold);
  color: var(--gold);
}

.filter-group {
  display: flex;
  gap: 4px;
}

.filter-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: all 0.2s;
}
.filter-btn:hover {
  color: var(--cream);
  border-color: var(--gold-dim);
}
.filter-btn.active {
  color: var(--gold);
  border-color: var(--gold);
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.page-size-label {
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.08em;
  margin-right: 4px;
}

.page-size-btn {
  min-width: 36px;
  height: 30px;
  padding: 0 6px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 12px;
  letter-spacing: 0.06em;
  transition: color 0.15s, border-color 0.15s;
}
.page-size-btn:hover {
  color: var(--cream);
  border-color: var(--gold-dim);
}
.page-size-btn.active {
  color: var(--gold);
  border-color: var(--gold);
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: rgba(212,175,55,0.06);
  border: 1px solid var(--gold-dim);
  margin-bottom: 16px;
  font-size: 13px;
  letter-spacing: 0.08em;
}
.filter-label { color: var(--gold); }
.filter-clear {
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: 12px;
  letter-spacing: 0.1em;
}
.filter-clear:hover { color: var(--cream); }

.error-message {
  padding: 12px 16px;
  background: rgba(200, 100, 100, 0.1);
  border: 1px solid rgba(200, 100, 100, 0.3);
  color: #e88;
  font-size: 13px;
  letter-spacing: 0.04em;
  margin-bottom: 16px;
}

.loading {
  text-align: center;
  padding: 48px;
  color: var(--muted);
  font-size: 14px;
  letter-spacing: 0.08em;
}

.translation-list {
  margin-bottom: 24px;
}

.empty-state {
  text-align: center;
  padding: 64px 24px;
  border: 1px dashed var(--gold-dim);
}

.empty-text {
  color: var(--muted);
  font-size: 14px;
  letter-spacing: 0.06em;
  margin-bottom: 20px;
}

.btn-start {
  padding: 12px 28px;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid var(--gold);
  color: var(--gold);
  font-size: 13px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-start:hover {
  background: rgba(212, 175, 55, 0.2);
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box {
    max-width: none;
  }
  .filter-group {
    justify-content: center;
  }
  .page-size-selector {
    justify-content: center;
    margin-left: 0;
  }
}
</style>
