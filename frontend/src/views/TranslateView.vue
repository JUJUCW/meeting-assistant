<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import { uploadPdf, getTranslateStatus, getDownloadUrl, deleteJob, listJobs } from '../api/translate'
import type { TranslateStatus, TranslateJob } from '../api/translate'

const jobs = ref<TranslateJob[]>([])
const isDragging = ref(false)
const file = ref<File | null>(null)
const jobId = ref<string | null>(null)
const status = ref<TranslateStatus | null>(null)
const uploading = ref(false)
const error = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

const progressLabel = computed(() => {
  const p = status.value?.progress
  if (!p || p === 'pending') return '等待中...'
  if (p === 'detecting') return '分析文件類型...'
  if (p === 'extracting') return '提取文字區塊...'
  if (p === 'ocr') return 'OCR 辨識文字...'
  if (p === 'translating') {
    const { done, total } = status.value!
    return total > 0 ? `翻譯中 (${done} / ${total} 個區塊)` : '翻譯中...'
  }
  if (p === 'rebuilding') return '重建文件...'
  if (p === 'done') return '翻譯完成'
  return p
})

const progressPercent = computed(() => {
  if (!status.value) return 0
  const { progress, done, total } = status.value
  if (progress === 'done') return 100
  if (progress === 'translating' && total > 0) return Math.round((done / total) * 80) + 15
  if (progress === 'rebuilding') return 95
  if (progress === 'extracting' || progress === 'ocr') return 10
  if (progress === 'detecting') return 5
  return 0
})

const isDone = computed(() => status.value?.status === 'done')
const isProcessing = computed(() =>
  status.value?.status === 'pending' || status.value?.status === 'processing'
)

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPolling(id: string) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const s = await getTranslateStatus(id)
      status.value = s
      if (s.status === 'done' || s.status === 'error') {
        stopPolling()
        loadJobs()
      }
    } catch {
      stopPolling()
    }
  }, 2000)
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  const dropped = e.dataTransfer?.files[0]
  if (dropped?.type === 'application/pdf') {
    file.value = dropped
  } else {
    error.value = '請上傳 PDF 格式的檔案'
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const picked = input.files?.[0]
  if (picked) file.value = picked
  input.value = ''
}

async function submit() {
  if (!file.value) return
  error.value = ''
  uploading.value = true
  try {
    const res = await uploadPdf(file.value)
    jobId.value = res.job_id
    status.value = { status: 'pending', progress: 'pending', total: 0, done: 0, source_lang: null, error: null }
    startPolling(res.job_id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '上傳失敗'
  } finally {
    uploading.value = false
  }
}

function download(fmt: 'pdf' | 'docx') {
  if (!jobId.value) return
  const url = getDownloadUrl(jobId.value, fmt)
  const a = document.createElement('a')
  a.href = url
  a.download = `translated.${fmt}`
  a.click()
}

async function loadJobs() {
  try {
    const res = await listJobs()
    jobs.value = res.jobs
  } catch { /* ignore */ }
}

async function onDeleteJob(id: string) {
  try {
    await deleteJob(id)
    jobs.value = jobs.value.filter(j => j.id !== id)
  } catch { /* ignore */ }
}

function reset() {
  if (jobId.value) deleteJob(jobId.value).catch(() => {})
  stopPolling()
  file.value = null
  jobId.value = null
  status.value = null
  error.value = ''
  uploading.value = false
  loadJobs()
}

onMounted(loadJobs)
onUnmounted(() => stopPolling())
</script>

<template>
  <div>
    <AppHeader
      eyebrow="Document"
      title="文件翻譯"
      subtitle="PDF Translation"
      :show-back="true"
      back-to="/"
      back-label="← 返回首頁"
    />

    <!-- Upload zone -->
    <template v-if="!jobId">
      <div
        class="drop-zone"
        :class="{ dragging: isDragging, 'has-file': !!file }"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="onDrop"
        @click="($refs.fileInput as HTMLInputElement).click()"
      >
        <input
          ref="fileInput"
          type="file"
          accept="application/pdf"
          style="display:none"
          @change="onFileChange"
        />
        <template v-if="file">
          <div class="drop-icon">📄</div>
          <div class="drop-filename">{{ file.name }}</div>
          <div class="drop-hint">點擊更換檔案</div>
        </template>
        <template v-else>
          <div class="drop-icon">⊕</div>
          <div class="drop-primary">拖曳 PDF 至此，或點擊選擇</div>
          <div class="drop-hint">支援文字型與掃描型 PDF・最大 50 MB</div>
        </template>
      </div>

      <div v-if="error" class="translate-error">{{ error }}</div>

      <div class="translate-actions">
        <button class="btn-edit" :disabled="!file || uploading" @click="submit">
          {{ uploading ? '上傳中...' : '開始翻譯' }}
        </button>
      </div>
    </template>

    <!-- Progress -->
    <template v-else-if="isProcessing">
      <div class="translate-card">
        <div class="progress-label">{{ progressLabel }}</div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }" />
        </div>
        <div class="progress-sub">
          翻譯目標語言：繁體中文
          <span v-if="status?.source_lang"> · 偵測來源語言：{{ status.source_lang }}</span>
        </div>
      </div>
    </template>

    <!-- Done -->
    <template v-else-if="isDone">
      <div class="translate-card">
        <div class="done-title">翻譯完成</div>
        <div class="done-sub">
          來源語言：{{ status?.source_lang ?? '未知' }} →
          繁體中文
        </div>
        <div class="download-row">
          <button class="btn-edit" @click="download('pdf')">下載 PDF</button>
          <button class="btn-edit" @click="download('docx')">下載 DOCX</button>
        </div>
        <button class="btn-reset" @click="reset">翻譯另一份文件</button>
      </div>
    </template>

    <!-- Error -->
    <template v-else-if="status?.status === 'error'">
      <div class="translate-card error-card">
        <div class="done-title error-title">翻譯失敗</div>
        <div class="translate-error">{{ status.error }}</div>
        <button class="btn-reset" @click="reset">重新嘗試</button>
      </div>
    </template>

    <!-- History list -->
    <div v-if="jobs.length > 0 && !jobId" class="history-section">
      <div class="history-title">翻譯紀錄</div>
      <div v-for="job in jobs" :key="job.id" class="history-item">
        <div class="history-item-info">
          <div class="history-filename">{{ job.filename }}</div>
          <div class="history-meta">
            {{ job.created_at.replace('T', ' ').slice(0, 16) }}
            <span v-if="job.source_lang"> · {{ job.source_lang }} → 繁體中文</span>
            <span v-if="job.status === 'error'" class="history-error-badge">失敗</span>
          </div>
        </div>
        <div class="history-item-actions">
          <template v-if="job.status === 'done'">
            <a :href="`/translate/download/${job.id}/pdf`" download class="btn-edit history-btn">PDF</a>
            <a :href="`/translate/download/${job.id}/docx`" download class="btn-edit history-btn">DOCX</a>
          </template>
          <button class="btn-delete history-btn" @click="onDeleteJob(job.id)">刪除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drop-zone {
  border: 1px dashed var(--gold-dim);
  padding: 52px 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  margin-bottom: 20px;
  position: relative;
}
.drop-zone:hover,
.drop-zone.dragging {
  border-color: var(--gold);
  background: rgba(212, 175, 55, 0.04);
}
.drop-zone.has-file {
  border-style: solid;
  border-color: rgba(212, 175, 55, 0.4);
}
.drop-icon {
  font-size: 28px;
  margin-bottom: 12px;
  color: var(--gold);
}
.drop-primary {
  font-size: 14px;
  color: var(--cream);
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}
.drop-filename {
  font-size: 14px;
  color: var(--gold);
  letter-spacing: 0.06em;
  margin-bottom: 6px;
  word-break: break-all;
}
.drop-hint {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.08em;
}

.translate-actions {
  display: flex;
  justify-content: flex-end;
}
.translate-actions .btn-edit:disabled {
  opacity: 0.4;
  cursor: default;
}

.translate-error {
  font-size: 12px;
  color: #e88;
  letter-spacing: 0.05em;
  margin-bottom: 16px;
  padding: 10px 14px;
  border: 1px solid rgba(200, 120, 120, 0.3);
}

.translate-card {
  border: 1px solid var(--gold-dim);
  padding: 32px 28px;
  position: relative;
}
.translate-card::before,
.translate-card::after {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  border-color: var(--gold);
  border-style: solid;
}
.translate-card::before { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
.translate-card::after  { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }

.progress-label {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--cream);
  letter-spacing: 0.08em;
  margin-bottom: 20px;
}
.progress-track {
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  margin-bottom: 14px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--gold);
  transition: width 0.6s ease;
}
.progress-sub {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.08em;
}

.done-title {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--cream);
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}
.done-sub {
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.08em;
  margin-bottom: 28px;
}
.download-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.btn-reset {
  font-family: var(--font-body);
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}
.btn-reset:hover { color: var(--cream); }

.error-card { border-color: rgba(200, 120, 120, 0.4); }
.error-title { color: #e88; }

.history-section {
  margin-top: 40px;
  border-top: 1px solid var(--gold-dim);
  padding-top: 24px;
}
.history-title {
  font-size: 11px;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 16px;
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.history-item:last-child { border-bottom: none; }
.history-item-info { flex: 1; min-width: 0; }
.history-filename {
  font-size: 13px;
  color: var(--cream);
  letter-spacing: 0.04em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}
.history-meta {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.06em;
}
.history-error-badge {
  color: #e88;
  margin-left: 6px;
}
.history-item-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  align-items: center;
}
.history-btn {
  font-size: 10px;
  padding: 4px 10px;
  text-decoration: none;
}
</style>
