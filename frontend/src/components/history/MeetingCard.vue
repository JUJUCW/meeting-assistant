<script setup lang="ts">
import { ref } from 'vue'
import InlineEdit from '../shared/InlineEdit.vue'
import TagPopover from './TagPopover.vue'
import { patchMeetingTitle, patchMeetingTags } from '../../api/meetings'
import type { MeetingListItem } from '../../types'
import { useCategories } from '../../composables/useCategories'

const props = defineProps<{ meeting: MeetingListItem }>()
const emit = defineEmits<{
  (e: 'open', id: string): void
  (e: 'deleted', id: string): void
  (e: 'filter', type: 'category' | 'tag', value: string): void
  (e: 'updated', id: string, patch: Partial<MeetingListItem>): void
}>()

const { categories } = useCategories()

const showDeleteConfirm = ref(false)
const popoverAnchorRect = ref<DOMRect | null>(null)
const title = ref(props.meeting.title ?? '')

function formatDate(s: string) {
  return (s ?? '').replace('T', ' ').slice(0, 16)
}

function categoryName(id?: string | null) {
  return categories.value.find(c => c.id === id)?.name ?? null
}

async function onTitleSave(val: string) {
  try {
    await patchMeetingTitle(props.meeting.id, val)
    emit('updated', props.meeting.id, { title: val })
  } catch {
    title.value = props.meeting.title ?? ''
  }
}

function openTagPopover(e: MouseEvent) {
  popoverAnchorRect.value = (e.currentTarget as HTMLElement).getBoundingClientRect()
}

async function onTagSave(payload: { categoryId: string | null; tags: string[] }) {
  popoverAnchorRect.value = null
  try {
    await patchMeetingTags(props.meeting.id, { category_id: payload.categoryId ?? undefined, tags: payload.tags })
    emit('updated', props.meeting.id, { category_id: payload.categoryId ?? undefined, tags: payload.tags })
  } catch { /* ignore */ }
}
</script>

<template>
  <div class="meeting-card">
    <!-- Top row -->
    <div class="meeting-card-top">
      <div class="meeting-date" @click="emit('open', meeting.id)">
        {{ formatDate(meeting.created_at) }}
      </div>
      <div class="meeting-card-actions">
        <button class="btn-tag-edit" @click="openTagPopover">＋ 標籤</button>
        <button class="btn-edit" @click="emit('open', meeting.id)">查看</button>
        <button class="btn-delete" @click="showDeleteConfirm = true">刪除</button>
      </div>
    </div>

    <!-- Editable title -->
    <InlineEdit
      v-model="title"
      placeholder="未命名會議"
      display-class="meeting-title"
      input-class="meeting-title-input"
      @save="onTitleSave"
    />

    <!-- Badges -->
    <div class="badges">
      <span class="badge badge-decisions">{{ meeting.decision_count ?? 0 }} 決議</span>
      <span class="badge badge-actions">{{ meeting.action_item_count ?? 0 }} 行動項目</span>
      <span v-if="(meeting.pending_action_item_count ?? 0) > 0" class="badge badge-pending">
        {{ meeting.pending_action_item_count }} 待處理
      </span>
    </div>

    <!-- Tag chips -->
    <div v-if="meeting.category_id || (meeting.tags ?? []).length > 0" class="card-tags">
      <span
        v-if="meeting.category_id"
        class="tag-chip category-chip"
        @click="emit('filter', 'category', meeting.category_id!)"
      >{{ categoryName(meeting.category_id) }}</span>
      <span
        v-for="tag in meeting.tags"
        :key="tag"
        class="tag-chip"
        @click="emit('filter', 'tag', tag)"
      >{{ tag }}</span>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDeleteConfirm" class="delete-confirm visible">
      <span class="delete-confirm-text">確認刪除此會議？</span>
      <button class="btn-confirm-delete" @click="emit('deleted', meeting.id)">確認</button>
      <button class="btn-cancel-delete" @click="showDeleteConfirm = false">取消</button>
    </div>

    <!-- Tag popover -->
    <TagPopover
      v-if="popoverAnchorRect"
      :meeting-id="meeting.id"
      :anchor-rect="popoverAnchorRect"
      :initial-category-id="meeting.category_id"
      :initial-tags="meeting.tags"
      @save="onTagSave"
      @close="popoverAnchorRect = null"
    />
  </div>
</template>

<style scoped>
.meeting-card {
  background: var(--card-bg);
  border: 1px solid var(--gold-dim);
  padding: 24px 28px;
  position: relative;
  transition: border-color 0.25s, box-shadow 0.25s;
  margin-bottom: 16px;
}
.meeting-card::before, .meeting-card::after {
  content: '';
  position: absolute;
  width: 14px; height: 14px;
  border-color: var(--gold);
  border-style: solid;
}
.meeting-card::before { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
.meeting-card::after  { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
.meeting-card:hover { border-color: rgba(212,175,55,0.6); box-shadow: var(--gold-glow); }

.meeting-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}
.meeting-date {
  font-family: var(--font-display);
  font-size: 17px;
  color: var(--cream);
  letter-spacing: 0.08em;
  cursor: pointer;
}
.meeting-date:hover { color: var(--gold); }

.meeting-card-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.card-tags {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.tag-chip {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  background: #2a2a2a;
  color: #aaa;
  border: 1px solid transparent;
  transition: opacity 0.15s;
  user-select: none;
}
.tag-chip:hover { opacity: 0.8; }
.tag-chip.category-chip { background: #1d3a5e; color: #6ab0f5; }
.tag-chip.filter-active { outline: 2px solid rgba(212,175,55,0.6); outline-offset: 1px; }

.delete-confirm {
  display: none;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(200,120,120,0.2);
}
.delete-confirm.visible { display: flex; }
.delete-confirm-text { font-size: 12px; letter-spacing: 0.08em; color: #e88; flex: 1; }

.btn-confirm-delete {
  font-family: var(--font-body);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: rgba(180,60,60,0.2);
  border: 1px solid rgba(200,120,120,0.5);
  color: #e88;
  padding: 4px 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-confirm-delete:hover { background: rgba(180,60,60,0.35); }

.btn-cancel-delete {
  font-family: var(--font-body);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: transparent;
  border: 1px solid var(--gold-dim);
  color: var(--muted);
  padding: 4px 12px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.btn-cancel-delete:hover { border-color: var(--gold); color: var(--cream); }

:deep(.meeting-title) {
  font-size: 15px;
  color: var(--cream);
  letter-spacing: 0.04em;
  cursor: text;
  margin-bottom: 12px;
  border-bottom: 1px solid transparent;
  display: inline-block;
  transition: border-color 0.2s;
  min-height: 1.2em;
}
:deep(.meeting-title):hover { border-bottom-color: var(--gold-dim); }

:deep(.meeting-title-input) {
  font-size: 15px;
  color: var(--cream);
  letter-spacing: 0.04em;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--gold);
  outline: none;
  width: 100%;
  padding: 0;
  margin-bottom: 12px;
  display: block;
}
</style>
