<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import InlineEdit from '../components/shared/InlineEdit.vue'
import SentenceTable from '../components/translation/SentenceTable.vue'
import { useTranslations } from '../composables/useTranslations'
import { getAudioUrl, getExportUrl } from '../api/translations'
import type { Translation } from '../types/translation'

const route = useRoute()
const router = useRouter()
const { get, updateName, loading, error } = useTranslations()

const translation = ref<Translation | null>(null)
const name = ref('')

const id = computed(() => route.params.id as string)

const stats = computed(() => {
  if (!translation.value) return null
  const sentences = translation.value.sentences
  const avgConfidence = sentences.length > 0
    ? sentences.reduce((sum, s) => sum + s.confidence, 0) / sentences.length
    : 0

  return {
    duration: formatDuration(translation.value.duration_sec),
    langPair: langPair(translation.value.source_lang, translation.value.target_lang),
    sentenceCount: sentences.length,
    avgConfidence: Math.round(avgConfidence * 100)
  }
})

const canDownloadAudio = computed(() =>
  translation.value?.status === 'completed' && translation.value.audio_path
)

function formatDuration(sec: number): string {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatDate(s: string): string {
  return (s ?? '').replace('T', ' ').slice(0, 19)
}

function langPair(src: string, tgt: string): string {
  const names: Record<string, string> = {
    'en': 'English',
    'zh-TW': '繁體中文',
    'zh': '中文',
    'ja': '日本語',
    'ko': '한국어',
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

async function loadTranslation(): Promise<void> {
  const result = await get(id.value)
  if (result) {
    translation.value = result
    name.value = result.name
  }
}

async function onNameSave(val: string): Promise<void> {
  const result = await updateName(id.value, val)
  if (result) {
    translation.value = result
  } else {
    name.value = translation.value?.name ?? ''
  }
}

function downloadAudio(): void {
  window.open(getAudioUrl(id.value), '_blank')
}

function exportDocx(): void {
  window.open(getExportUrl(id.value), '_blank')
}

function goBack(): void {
  router.push('/translation-history')
}

onMounted(() => {
  loadTranslation()
})
</script>

<template>
  <div>
    <AppHeader
      eyebrow="Detail"
      title="翻譯詳情"
      subtitle="Translation Detail"
      :show-back="true"
      back-to="/translation-history"
      back-label="← 返回列表"
    />

    <!-- Error state -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="loading">
      載入中...
    </div>

    <!-- Content -->
    <template v-else-if="translation">
      <!-- Header section -->
      <div class="detail-header">
        <div class="header-main">
          <div class="translation-id">{{ translation.id }}</div>
          <InlineEdit
            v-model="name"
            placeholder="未命名翻譯"
            display-class="translation-name"
            input-class="translation-name-input"
            @save="onNameSave"
          />
          <div class="translation-meta">
            <span class="meta-date">{{ formatDate(translation.started_at) }}</span>
            <span class="meta-status" :class="'status-' + translation.status">
              {{ statusLabel(translation.status) }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button
            class="btn-audio"
            :disabled="!canDownloadAudio"
            @click="downloadAudio"
          >
            下載音訊
          </button>
          <button class="btn-export" @click="exportDocx">
            匯出 DOCX
          </button>
        </div>
      </div>

      <!-- Stats cards -->
      <div v-if="stats" class="stats-row">
        <div class="stat-card">
          <div class="stat-label">總時長</div>
          <div class="stat-value">{{ stats.duration }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">語言對</div>
          <div class="stat-value">{{ stats.langPair }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">句數</div>
          <div class="stat-value">{{ stats.sentenceCount }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">平均信心</div>
          <div class="stat-value" :class="stats.avgConfidence >= 65 ? 'confidence-good' : 'confidence-low'">
            {{ stats.avgConfidence }}%
          </div>
        </div>
      </div>

      <!-- Sentences table -->
      <div class="sentences-section">
        <h3 class="section-title">逐句對照</h3>
        <SentenceTable :sentences="translation.sentences" :page-size="20" />
      </div>
    </template>

    <!-- Not found -->
    <div v-else class="not-found">
      <p>找不到此翻譯紀錄</p>
      <button class="btn-back" @click="goBack">返回列表</button>
    </div>
  </div>
</template>

<style scoped>
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

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 24px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--gold-dim);
  margin-bottom: 24px;
}

.header-main {
  flex: 1;
}

.translation-id {
  font-family: var(--font-display);
  font-size: 12px;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin-bottom: 8px;
}

:deep(.translation-name) {
  font-size: 20px;
  color: var(--cream);
  letter-spacing: 0.04em;
  cursor: text;
  margin-bottom: 8px;
  border-bottom: 1px solid transparent;
  display: inline-block;
  transition: border-color 0.2s;
  min-height: 1.2em;
}
:deep(.translation-name):hover {
  border-bottom-color: var(--gold-dim);
}

:deep(.translation-name-input) {
  font-size: 20px;
  color: var(--cream);
  letter-spacing: 0.04em;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--gold);
  outline: none;
  width: 100%;
  padding: 0;
  margin-bottom: 8px;
}

.translation-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-date {
  font-size: 13px;
  color: var(--muted);
  letter-spacing: 0.06em;
}

.meta-status {
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 3px 10px;
  border-radius: 2px;
}
.meta-status.status-in_progress {
  background: rgba(100, 200, 100, 0.15);
  color: #8c8;
}
.meta-status.status-completed {
  background: rgba(100, 150, 200, 0.15);
  color: #8ac;
}
.meta-status.status-interrupted {
  background: rgba(200, 100, 100, 0.15);
  color: #c88;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.btn-audio,
.btn-export {
  padding: 10px 18px;
  font-family: var(--font-body);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border: 1px solid;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-audio {
  background: transparent;
  border-color: var(--gold-dim);
  color: var(--muted);
}
.btn-audio:hover:not(:disabled) {
  border-color: var(--gold);
  color: var(--gold);
}
.btn-audio:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-export {
  background: rgba(212, 175, 55, 0.1);
  border-color: var(--gold);
  color: var(--gold);
}
.btn-export:hover {
  background: rgba(212, 175, 55, 0.2);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--gold-dim);
  text-align: center;
}

.stat-label {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--cream);
  letter-spacing: 0.06em;
}

.stat-value.confidence-good {
  color: #8c8;
}
.stat-value.confidence-low {
  color: #c88;
}

.sentences-section {
  margin-bottom: 32px;
}

.section-title {
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 16px;
}

.not-found {
  text-align: center;
  padding: 64px 24px;
  border: 1px dashed var(--gold-dim);
}

.not-found p {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 20px;
}

.btn-back {
  padding: 10px 24px;
  background: transparent;
  border: 1px solid var(--gold-dim);
  color: var(--muted);
  font-size: 13px;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-back:hover {
  border-color: var(--gold);
  color: var(--cream);
}

@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
  }
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
