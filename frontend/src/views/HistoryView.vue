<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import ServerWarning from '../components/layout/ServerWarning.vue'
import SearchBar from '../components/history/SearchBar.vue'
import MeetingList from '../components/history/MeetingList.vue'
import Pagination from '../components/history/Pagination.vue'
import DetailHeader from '../components/detail/DetailHeader.vue'
import TranscriptSection from '../components/detail/TranscriptSection.vue'
import SummarySection from '../components/detail/SummarySection.vue'
import DecisionList from '../components/detail/DecisionList.vue'
import ActionItemList from '../components/detail/ActionItemList.vue'
import TranscriptionProgress from '../components/upload/TranscriptionProgress.vue'
import { useMeetings } from '../composables/useMeetings'
import { useMeetingDetail } from '../composables/useMeetingDetail'
import { useCategories } from '../composables/useCategories'
import { useTranscriptionJob } from '../composables/useTranscriptionJob'
import { exportMarkdown, exportJson } from '../utils/export'
import type { MeetingListItem, Decision, ActionItem } from '../types'

const {
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
  remove,
  updateLocal,
  setPage,
  setPageSize,
} = useMeetings()

const { meeting, load: loadDetail, close, updateTitle, addDecision, updateDecision, addAction, updateAction, toggleActionStatus, generateSummary, isSummaryLoading, summaryError } = useMeetingDetail()
const { load: loadCategories } = useCategories()
const { activeJob, dismiss } = useTranscriptionJob()
const showDetail = ref(false)

onMounted(async () => {
  await Promise.all([load(), loadCategories()])
})

// 轉錄完成時自動刷新列表
watch(() => activeJob.value?.status, (status) => {
  if (status === 'done') load()
})

async function openDetail(id: string) {
  await loadDetail(id)
  showDetail.value = true
}

function backToList() {
  showDetail.value = false
  close()
  load()
}

async function onDeleted(id: string) {
  await remove(id)
}

function onUpdated(id: string, patch: Partial<MeetingListItem>) {
  updateLocal(id, patch)
}

function onFilter(type: 'category' | 'tag', value: string) {
  setFilter(type, value)
}

async function onDecisionSave(id: string, body: Partial<Decision>) {
  try { await updateDecision(id, body) } catch { /* error shown in component */ }
}

async function onDecisionAdd(body: Partial<Decision>) {
  try { await addDecision(body) } catch { /* error shown in component */ }
}

async function onActionSave(id: string, body: Partial<ActionItem>) {
  try { await updateAction(id, body) } catch { /* error shown in component */ }
}

async function onActionAdd(body: Partial<ActionItem>) {
  try { await addAction(body) } catch { /* error shown in component */ }
}

async function onToggle(id: string) {
  try { await toggleActionStatus(id) } catch { /* ignore */ }
}

async function onTitleSave(val: string) {
  try {
    await updateTitle(val)
    if (meeting.value) updateLocal(meeting.value.id, { title: val })
  } catch { /* ignore */ }
}
</script>

<template>
  <div>
    <!-- List View -->
    <template v-if="!showDetail">
      <AppHeader
        eyebrow="Archive"
        title="歷史紀錄"
        subtitle="Meeting Records"
        :show-back="true"
        back-to="/"
        back-label="← 返回首頁"
      />

      <ServerWarning :visible="serverError" />

      <TranscriptionProgress
        v-if="activeJob"
        :status="activeJob.status"
        :estimated-secs="activeJob.estimatedSecs"
        :elapsed-secs="activeJob.elapsedSecs"
        :error="activeJob.error"
        @dismiss="dismiss"
      />

      <div v-if="activeFilter" class="filter-bar">
        <span class="filter-label">
          篩選：{{ activeFilter.type === 'category' ? '分類' : '標籤' }} — {{ activeFilter.value }}
        </span>
        <button class="filter-clear" @click="clearFilter">✕ 清除</button>
      </div>

      <div class="list-toolbar">
        <SearchBar :model-value="searchQuery" @update:model-value="search" />
        <div class="page-size-selector">
          <span class="page-size-label">每頁</span>
          <button
            v-for="n in [10, 20, 50]"
            :key="n"
            class="page-size-btn"
            :class="{ active: pageSize === n }"
            @click="setPageSize(n)"
          >{{ n }}</button>
        </div>
      </div>

      <MeetingList
        :meetings="meetings"
        :is-loading="isLoading"
        @open="openDetail"
        @deleted="onDeleted"
        @filter="onFilter"
        @updated="onUpdated"
      />

      <Pagination
        v-if="total > 0"
        :page="page"
        :total-pages="totalPages"
        :total="total"
        :page-size="pageSize"
        @update:page="setPage"
      />
    </template>

    <!-- Detail View -->
    <template v-else-if="meeting">
      <DetailHeader
        :meeting="meeting"
        @back="backToList"
        @title-save="onTitleSave"
        @export-md="exportMarkdown(meeting!)"
        @export-json="exportJson(meeting!)"
      />

      <TranscriptSection v-if="meeting.transcript" :transcript="meeting.transcript" />

      <SummarySection
        :meeting-id="meeting.id"
        :summary="meeting.summary"
        :is-loading="isSummaryLoading"
        :error="summaryError"
        @generate="generateSummary"
      />

      <DecisionList
        :decisions="meeting.decisions ?? []"
        @save="onDecisionSave"
        @add="onDecisionAdd"
      />

      <ActionItemList
        :items="meeting.action_items ?? []"
        @save="onActionSave"
        @toggle="onToggle"
        @add="onActionAdd"
      />
    </template>
  </div>
</template>

<style scoped>
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

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.list-toolbar :deep(.search-bar) {
  flex: 1;
  margin-bottom: 0;
}

@media (max-width: 600px) {
  .list-toolbar {
    flex-wrap: wrap;
  }
  .list-toolbar :deep(.search-bar) {
    width: 100%;
    flex: none;
  }
  .page-size-selector {
    margin-left: auto;
  }
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
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
</style>
