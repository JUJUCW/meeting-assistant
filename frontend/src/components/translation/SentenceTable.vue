<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Sentence } from '../../types/translation'

const props = defineProps<{
  sentences: Sentence[]
  pageSize?: number
}>()

const searchQuery = ref('')
const currentPage = ref(1)
const itemsPerPage = computed(() => props.pageSize ?? 20)

// Filter sentences by search query
const filteredSentences = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.sentences
  }
  const q = searchQuery.value.toLowerCase()
  return props.sentences.filter(s =>
    s.original_text.toLowerCase().includes(q) ||
    s.translated_text.toLowerCase().includes(q)
  )
})

// Paginate
const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredSentences.value.length / itemsPerPage.value))
)

const paginatedSentences = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  return filteredSentences.value.slice(start, start + itemsPerPage.value)
})

// Reset to page 1 when search changes
watch(searchQuery, () => {
  currentPage.value = 1
})

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function confidenceClass(confidence: number): string {
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.65) return 'confidence-medium'
  return 'confidence-low'
}

function confidencePercent(confidence: number): string {
  return `${Math.round(confidence * 100)}%`
}
</script>

<template>
  <div class="sentence-table-container">
    <!-- Search bar -->
    <div class="table-toolbar">
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜尋原文或譯文..."
          class="search-input"
        />
      </div>
      <div class="result-count">
        {{ filteredSentences.length }} / {{ sentences.length }} 句
      </div>
    </div>

    <!-- Table -->
    <div class="table-wrapper">
      <table class="sentence-table">
        <thead>
          <tr>
            <th class="col-seq">#</th>
            <th class="col-time">時間</th>
            <th class="col-original">原文</th>
            <th class="col-translated">譯文</th>
            <th class="col-confidence">信心</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sentence in paginatedSentences" :key="sentence.sentence_id">
            <td class="col-seq">{{ sentence.sequence }}</td>
            <td class="col-time">{{ formatTime(sentence.offset_sec) }}</td>
            <td class="col-original">{{ sentence.original_text }}</td>
            <td class="col-translated">{{ sentence.translated_text }}</td>
            <td class="col-confidence">
              <div class="confidence-bar" :class="confidenceClass(sentence.confidence)">
                <div
                  class="confidence-fill"
                  :style="{ width: confidencePercent(sentence.confidence) }"
                ></div>
                <span class="confidence-text">{{ confidencePercent(sentence.confidence) }}</span>
              </div>
            </td>
          </tr>
          <tr v-if="paginatedSentences.length === 0">
            <td colspan="5" class="no-data">
              {{ searchQuery ? '找不到符合的句子' : '尚無句子' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        class="page-btn"
        :disabled="currentPage <= 1"
        @click="currentPage--"
      >
        ← 上一頁
      </button>
      <span class="page-info">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <button
        class="page-btn"
        :disabled="currentPage >= totalPages"
        @click="currentPage++"
      >
        下一頁 →
      </button>
    </div>
  </div>
</template>

<style scoped>
.sentence-table-container {
  margin-top: 24px;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.search-box {
  flex: 1;
  max-width: 400px;
}

.search-input {
  width: 100%;
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

.result-count {
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.08em;
}

.table-wrapper {
  overflow-x: auto;
}

.sentence-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.sentence-table th,
.sentence-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid rgba(212, 175, 55, 0.1);
}

.sentence-table th {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.02);
}

.sentence-table td {
  color: var(--cream);
  vertical-align: top;
}

.col-seq {
  width: 50px;
  color: var(--muted) !important;
  font-family: var(--font-display);
}

.col-time {
  width: 70px;
  font-family: var(--font-display);
  color: var(--gold) !important;
}

.col-original,
.col-translated {
  min-width: 200px;
}

.col-confidence {
  width: 100px;
}

.confidence-bar {
  position: relative;
  height: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  transition: width 0.3s;
}

.confidence-high .confidence-fill {
  background: rgba(100, 200, 100, 0.4);
}

.confidence-medium .confidence-fill {
  background: rgba(220, 180, 80, 0.4);
}

.confidence-low .confidence-fill {
  background: rgba(200, 100, 100, 0.4);
}

.confidence-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--cream);
}

.no-data {
  text-align: center;
  color: var(--muted);
  font-style: italic;
  padding: 32px 12px !important;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(212, 175, 55, 0.1);
}

.page-btn {
  font-family: var(--font-body);
  font-size: 12px;
  letter-spacing: 0.08em;
  background: transparent;
  border: 1px solid var(--gold-dim);
  color: var(--muted);
  padding: 6px 14px;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.page-btn:hover:not(:disabled) {
  color: var(--gold);
  border-color: var(--gold);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.1em;
}

@media (max-width: 768px) {
  .table-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box {
    max-width: none;
  }
  .result-count {
    text-align: right;
  }
}
</style>
