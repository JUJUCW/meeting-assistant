<script setup lang="ts">
import { ref } from 'vue'
import { getAudioUrl, getExportUrl } from '../../api/translations'
import type { TranslationListItem } from '../../types/translation'

const props = defineProps<{ translation: TranslationListItem }>()
const emit = defineEmits<{
  (e: 'open', id: string): void
  (e: 'deleted', id: string): void
}>()

const showDeleteConfirm = ref(false)

function formatDate(s: string): string {
  return (s ?? '').replace('T', ' ').slice(0, 16)
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function langPair(src: string, tgt: string): string {
  const names: Record<string, string> = {
    'en': 'EN',
    'zh-TW': '繁中',
    'zh': '中',
    'ja': '日',
    'ko': '韓',
  }
  return `${names[src] ?? src} → ${names[tgt] ?? tgt}`
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    'in_progress': '錄音中',
    'completed': '已完成',
    'interrupted': '已中斷',
  }
  return labels[status] ?? status
}

function downloadAudio(): void {
  window.open(getAudioUrl(props.translation.id), '_blank')
}

function exportDocx(): void {
  window.open(getExportUrl(props.translation.id), '_blank')
}
</script>

<template>
  <div class="translation-card" :class="{ 'is-in-progress': translation.status === 'in_progress' }">
    <!-- Top row -->
    <div class="card-top">
      <div class="card-id" @click="emit('open', translation.id)">
        {{ translation.id }}
      </div>
      <div class="card-actions">
        <button class="btn-view" @click="emit('open', translation.id)">查看</button>
        <button
          class="btn-audio"
          :disabled="translation.status !== 'completed'"
          @click="downloadAudio"
        >音訊</button>
        <button class="btn-export" @click="exportDocx">匯出</button>
        <button class="btn-delete" @click="showDeleteConfirm = true">刪除</button>
      </div>
    </div>

    <!-- Name and date -->
    <div class="card-name" @click="emit('open', translation.id)">
      {{ translation.name || '未命名翻譯' }}
    </div>
    <div class="card-date">{{ formatDate(translation.started_at) }}</div>

    <!-- Badges -->
    <div class="badges">
      <span class="badge badge-status" :class="'status-' + translation.status">
        {{ statusLabel(translation.status) }}
      </span>
      <span class="badge badge-lang">{{ langPair(translation.source_lang, translation.target_lang) }}</span>
      <span class="badge badge-duration">{{ formatDuration(translation.duration_sec) }}</span>
      <span class="badge badge-sentences">{{ translation.sentence_count }} 句</span>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDeleteConfirm" class="delete-confirm visible">
      <span class="delete-confirm-text">確認刪除此翻譯？</span>
      <button class="btn-confirm-delete" @click="emit('deleted', translation.id)">確認</button>
      <button class="btn-cancel-delete" @click="showDeleteConfirm = false">取消</button>
    </div>
  </div>
</template>

<style scoped>
.translation-card {
  background: var(--card-bg);
  border: 1px solid var(--gold-dim);
  padding: 24px 28px;
  position: relative;
  transition: border-color 0.25s, box-shadow 0.25s;
  margin-bottom: 16px;
}
.translation-card::before, .translation-card::after {
  content: '';
  position: absolute;
  width: 14px; height: 14px;
  border-color: var(--gold);
  border-style: solid;
}
.translation-card::before { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
.translation-card::after  { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
.translation-card:hover { border-color: rgba(212,175,55,0.6); box-shadow: var(--gold-glow); }

.translation-card.is-in-progress {
  border-color: rgba(100, 200, 100, 0.4);
}
.translation-card.is-in-progress::before,
.translation-card.is-in-progress::after {
  border-color: rgba(100, 200, 100, 0.6);
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}

.card-id {
  font-family: var(--font-display);
  font-size: 13px;
  color: var(--muted);
  letter-spacing: 0.1em;
  cursor: pointer;
}
.card-id:hover { color: var(--gold); }

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.card-name {
  font-size: 16px;
  color: var(--cream);
  letter-spacing: 0.04em;
  cursor: pointer;
  margin-bottom: 4px;
}
.card-name:hover { color: var(--gold); }

.card-date {
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.06em;
  margin-bottom: 12px;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  font-size: 11px;
  letter-spacing: 0.08em;
  border-radius: 2px;
  text-transform: uppercase;
}

.badge-status {
  background: rgba(100, 200, 100, 0.15);
  color: #7c7;
}
.badge-status.status-in_progress {
  background: rgba(100, 200, 100, 0.2);
  color: #8e8;
  animation: pulse 2s infinite;
}
.badge-status.status-completed {
  background: rgba(100, 150, 200, 0.15);
  color: #8ac;
}
.badge-status.status-interrupted {
  background: rgba(200, 100, 100, 0.15);
  color: #c88;
}

.badge-lang {
  background: rgba(212, 175, 55, 0.1);
  color: var(--gold);
}

.badge-duration,
.badge-sentences {
  background: rgba(255, 255, 255, 0.05);
  color: var(--muted);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.btn-view,
.btn-audio,
.btn-export,
.btn-delete {
  font-family: var(--font-body);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: transparent;
  border: 1px solid var(--gold-dim);
  color: var(--muted);
  padding: 4px 10px;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.btn-view:hover,
.btn-audio:hover:not(:disabled),
.btn-export:hover {
  color: var(--gold);
  border-color: var(--gold);
}

.btn-audio:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-delete:hover {
  color: #e88;
  border-color: rgba(200, 120, 120, 0.5);
}

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

@media (max-width: 600px) {
  .card-top { flex-wrap: wrap; }
  .card-id { width: 100%; margin-bottom: 8px; }
  .card-actions { margin-left: auto; }
}
</style>
