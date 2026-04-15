<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import { useLiveTranslate } from '../composables/useLiveTranslate'

const router = useRouter()
const {
  sentences,
  status,
  error,
  translationId,
  start,
  stop,
  reset
} = useLiveTranslate()

const recordingDuration = ref(0)
let durationTimer: ReturnType<typeof setInterval> | null = null

const statusText = computed(() => {
  switch (status.value) {
    case 'idle': return '準備就緒'
    case 'connecting': return '連線中...'
    case 'recording': return '錄音中'
    case 'processing': return '處理中...'
    case 'reconnecting': return '重新連線...'
    case 'completed': return '已完成'
    case 'error': return '發生錯誤'
    default: return ''
  }
})

const canStart = computed(() => status.value === 'idle' || status.value === 'completed' || status.value === 'error')
const canStop = computed(() => status.value === 'recording' || status.value === 'processing')
const isActive = computed(() => ['connecting', 'recording', 'processing', 'reconnecting'].includes(status.value))

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

async function handleStart(): Promise<void> {
  reset()
  recordingDuration.value = 0

  const id = await start()
  if (id) {
    // Start duration timer
    durationTimer = setInterval(() => {
      recordingDuration.value++
    }, 1000)
  }
}

function handleStop(): void {
  stop()
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
}

function goToDetail(): void {
  if (translationId.value) {
    router.push(`/translation/${translationId.value}`)
  }
}

function goToHistory(): void {
  router.push('/translation-history')
}

onUnmounted(() => {
  if (durationTimer) {
    clearInterval(durationTimer)
  }
})
</script>

<template>
  <div>
    <AppHeader
      eyebrow="Live"
      title="即時翻譯"
      subtitle="Live Translation"
      :show-back="true"
      back-to="/"
      back-label="← 返回首頁"
    />

    <!-- Status indicator -->
    <div class="status-section">
      <div class="status-indicator" :class="'status-' + status">
        <span class="status-dot"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div v-if="isActive" class="duration">
        {{ formatDuration(recordingDuration) }}
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- Control buttons -->
    <div class="controls">
      <button
        v-if="canStart"
        class="btn-start"
        @click="handleStart"
      >
        <span class="btn-icon">●</span>
        開始錄音
      </button>
      <button
        v-if="canStop"
        class="btn-stop"
        @click="handleStop"
      >
        <span class="btn-icon">■</span>
        停止錄音
      </button>
    </div>

    <!-- Sentences list -->
    <div class="sentences-section">
      <h3 class="section-title">
        即時辨識結果
        <span class="sentence-count">({{ sentences.length }} 句)</span>
      </h3>

      <div class="sentences-list">
        <div
          v-for="sentence in sentences"
          :key="sentence.sentence_id"
          class="sentence-item"
        >
          <div class="sentence-header">
            <span class="sentence-seq">#{{ sentence.sequence }}</span>
            <span class="sentence-confidence" :class="sentence.confidence >= 0.65 ? 'high' : 'low'">
              {{ Math.round(sentence.confidence * 100) }}%
            </span>
          </div>
          <div class="sentence-original">{{ sentence.original_text }}</div>
          <div class="sentence-translated">
            {{ sentence.translated_text || '翻譯中...' }}
          </div>
        </div>

        <div v-if="sentences.length === 0 && !isActive" class="no-sentences">
          點擊「開始錄音」開始即時翻譯
        </div>

        <div v-if="sentences.length === 0 && isActive" class="waiting">
          等待語音輸入...
        </div>
      </div>
    </div>

    <!-- Completion actions -->
    <div v-if="status === 'completed' && translationId" class="completion-actions">
      <button class="btn-detail" @click="goToDetail">
        查看詳情 →
      </button>
      <button class="btn-history" @click="goToHistory">
        查看歷史
      </button>
    </div>
  </div>
</template>

<style scoped>
.status-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--gold-dim);
  margin-bottom: 24px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--muted);
}

.status-idle .status-dot { background: var(--muted); }
.status-connecting .status-dot,
.status-reconnecting .status-dot {
  background: var(--gold);
  animation: blink 1s infinite;
}
.status-recording .status-dot {
  background: #e55;
  animation: pulse-dot 1.5s infinite;
}
.status-processing .status-dot {
  background: var(--gold);
  animation: blink 0.5s infinite;
}
.status-completed .status-dot { background: #7c7; }
.status-error .status-dot { background: #e55; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

.status-text {
  font-size: 14px;
  letter-spacing: 0.08em;
  color: var(--cream);
}

.duration {
  font-family: var(--font-display);
  font-size: 24px;
  color: var(--gold);
  letter-spacing: 0.1em;
}

.error-message {
  padding: 12px 16px;
  background: rgba(200, 100, 100, 0.1);
  border: 1px solid rgba(200, 100, 100, 0.3);
  color: #e88;
  font-size: 13px;
  letter-spacing: 0.04em;
  margin-bottom: 24px;
}

.controls {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 32px;
}

.btn-start,
.btn-stop {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 32px;
  font-family: var(--font-body);
  font-size: 14px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border: 2px solid;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-start {
  background: rgba(100, 200, 100, 0.1);
  border-color: rgba(100, 200, 100, 0.4);
  color: #8c8;
}
.btn-start:hover {
  background: rgba(100, 200, 100, 0.2);
  border-color: rgba(100, 200, 100, 0.6);
}

.btn-stop {
  background: rgba(200, 100, 100, 0.1);
  border-color: rgba(200, 100, 100, 0.4);
  color: #e88;
}
.btn-stop:hover {
  background: rgba(200, 100, 100, 0.2);
  border-color: rgba(200, 100, 100, 0.6);
}

.btn-icon {
  font-size: 12px;
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
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.sentence-count {
  font-size: 12px;
  color: var(--muted);
  font-weight: normal;
}

.sentences-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--gold-dim);
  background: rgba(255, 255, 255, 0.01);
}

.sentence-item {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(212, 175, 55, 0.1);
}
.sentence-item:last-child {
  border-bottom: none;
}

.sentence-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.sentence-seq {
  font-size: 11px;
  letter-spacing: 0.1em;
  color: var(--muted);
}

.sentence-confidence {
  font-size: 11px;
  letter-spacing: 0.08em;
  padding: 2px 8px;
  border-radius: 2px;
}
.sentence-confidence.high {
  background: rgba(100, 200, 100, 0.15);
  color: #7c7;
}
.sentence-confidence.low {
  background: rgba(200, 100, 100, 0.15);
  color: #c88;
}

.sentence-original {
  font-size: 14px;
  color: var(--cream);
  margin-bottom: 6px;
  line-height: 1.5;
}

.sentence-translated {
  font-size: 13px;
  color: var(--gold);
  line-height: 1.5;
  font-style: italic;
}

.no-sentences,
.waiting {
  padding: 48px 16px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
  letter-spacing: 0.06em;
}

.waiting {
  animation: fade 1.5s infinite;
}

@keyframes fade {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.completion-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--gold-dim);
}

.btn-detail,
.btn-history {
  padding: 10px 24px;
  font-family: var(--font-body);
  font-size: 13px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border: 1px solid;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-detail {
  background: rgba(212, 175, 55, 0.1);
  border-color: var(--gold);
  color: var(--gold);
}
.btn-detail:hover {
  background: rgba(212, 175, 55, 0.2);
}

.btn-history {
  background: transparent;
  border-color: var(--gold-dim);
  color: var(--muted);
}
.btn-history:hover {
  border-color: var(--gold);
  color: var(--cream);
}
</style>
