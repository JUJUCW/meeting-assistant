<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import ServerWarning from '../components/layout/ServerWarning.vue'
import SearchBar from '../components/history/SearchBar.vue'
import MeetingList from '../components/history/MeetingList.vue'
import DetailHeader from '../components/detail/DetailHeader.vue'
import TranscriptSection from '../components/detail/TranscriptSection.vue'
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
  displayedMeetings,
  searchQuery,
  activeFilter,
  isLoading,
  serverError,
  load,
  search,
  setFilter,
  remove,
  updateLocal,
} = useMeetings()

const { meeting, load: loadDetail, close, updateTitle, addDecision, updateDecision, addAction, updateAction, toggleActionStatus } = useMeetingDetail()
const { load: loadCategories } = useCategories()
const { activeJob, dismiss } = useTranscriptionJob()
const showDetail = ref(false)

onMounted(async () => {
  await Promise.all([load(), loadCategories()])
})

watch(searchQuery, (q) => search(q))

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
        <button class="filter-clear" @click="setFilter(activeFilter!.type, activeFilter!.value)">✕ 清除</button>
      </div>

      <SearchBar v-model="searchQuery" />

      <MeetingList
        :meetings="displayedMeetings"
        :is-loading="isLoading"
        @open="openDetail"
        @deleted="onDeleted"
        @filter="onFilter"
        @updated="onUpdated"
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
</style>
