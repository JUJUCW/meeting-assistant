<script setup lang="ts">
import { getMeetingDocxUrl } from '../../api/meetings'

const props = defineProps<{
  meetingId: string
  summary?: string
  isLoading: boolean
  error: string
}>()

defineEmits<{ (e: 'generate'): void }>()

function downloadDocx() {
  const a = document.createElement('a')
  a.href = getMeetingDocxUrl(props.meetingId)
  a.download = `${props.meetingId}.docx`
  a.click()
}
</script>

<template>
  <section class="summary-section">
    <div class="summary-header">
      <h3 class="summary-title">摘要</h3>
      <div class="summary-actions">
        <button class="action-btn" :disabled="isLoading" @click="$emit('generate')">
          {{ isLoading ? '產生中…' : summary ? '重新產生' : '產生摘要' }}
        </button>
        <button v-if="summary" class="action-btn download-btn" @click="downloadDocx">
          下載 .docx
        </button>
      </div>
    </div>

    <div v-if="error" class="summary-error">{{ error }}</div>

    <div v-if="isLoading" class="summary-placeholder">AI 分析中，請稍候…</div>
    <p v-else-if="summary" class="summary-body">{{ summary }}</p>
    <p v-else class="summary-placeholder">尚未產生摘要</p>
  </section>
</template>

<style scoped>
.summary-section {
  padding: 20px 16px;
  border-bottom: 1px solid var(--border);
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.summary-title {
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0;
}

.summary-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: transparent;
  border: 1px solid var(--gold-dim);
  color: var(--gold);
  font-size: 11px;
  letter-spacing: 0.08em;
  padding: 4px 10px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.action-btn:hover:not(:disabled) {
  background: rgba(212, 175, 55, 0.08);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.download-btn {
  border-color: rgba(255, 255, 255, 0.15);
  color: var(--muted);
}

.download-btn:hover {
  color: var(--cream);
  background: rgba(255, 255, 255, 0.04) !important;
}

.summary-body {
  font-size: 14px;
  line-height: 1.8;
  color: var(--cream);
  margin: 0;
  white-space: pre-wrap;
}

.summary-placeholder {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
  font-style: italic;
}

.summary-error {
  font-size: 12px;
  color: #e88;
  margin-bottom: 8px;
}
</style>
