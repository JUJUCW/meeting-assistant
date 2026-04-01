<script setup lang="ts">
import InlineEdit from '../shared/InlineEdit.vue'
import type { Meeting } from '../../types'

defineProps<{ meeting: Meeting }>()
const emit = defineEmits<{
  (e: 'back'): void
  (e: 'title-save', val: string): void
  (e: 'export-md'): void
  (e: 'export-json'): void
}>()

function formatDate(s: string) {
  return (s ?? '').replace('T', ' ').slice(0, 16)
}
</script>

<template>
  <div>
  <button class="back-btn" @click="emit('back')">← 返回列表</button>

  <div class="detail-header">
    <div>
      <div class="detail-date">{{ formatDate(meeting.created_at) }}</div>
      <InlineEdit
        :model-value="meeting.title ?? ''"
        placeholder="未命名會議"
        display-class="detail-title"
        input-class="detail-title-input"
        @save="emit('title-save', $event)"
      />
    </div>
    <div class="detail-actions">
      <button class="btn-edit" @click="emit('export-md')">匯出 MD</button>
      <button class="btn-edit" @click="emit('export-json')">匯出 JSON</button>
    </div>
  </div>
  </div>
</template>

<style scoped>
.back-btn {
  font-family: var(--font-body);
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--gold);
  background: transparent;
  border: none;
  cursor: pointer;
  opacity: 0.8;
  padding: 0;
  margin-bottom: 28px;
  transition: opacity 0.2s;
  display: block;
}
.back-btn:hover { opacity: 1; }

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 36px;
  gap: 16px;
}
.detail-date {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--gold-dim);
  letter-spacing: 0.12em;
  margin-bottom: 8px;
}
.detail-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

:deep(.detail-title) {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 400;
  color: var(--cream);
  letter-spacing: 0.08em;
  cursor: text;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
  min-width: 200px;
  min-height: 1.4em;
}
:deep(.detail-title):hover { border-bottom-color: var(--gold-dim); }

:deep(.detail-title-input) {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 400;
  color: var(--cream);
  letter-spacing: 0.08em;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--gold);
  outline: none;
  width: 100%;
  min-width: 200px;
  padding: 0;
}
</style>
