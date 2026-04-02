<script setup lang="ts">
import { computed } from 'vue'

const isMobile = typeof window !== 'undefined' && window.innerWidth <= 600

const props = defineProps<{
  page: number
  totalPages: number
  total: number
  pageSize: number
}>()

const emit = defineEmits<{
  (e: 'update:page', value: number): void
}>()

type PageToken = number | '...'

const pageTokens = computed<PageToken[]>(() => {
  const { page, totalPages } = props
  const delta = isMobile ? 1 : 2
  if (totalPages <= delta * 2 + 3) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }

  const tokens: PageToken[] = [1]
  const rangeStart = Math.max(2, page - delta)
  const rangeEnd = Math.min(totalPages - 1, page + delta)

  if (rangeStart > 2) tokens.push('...')
  for (let i = rangeStart; i <= rangeEnd; i++) tokens.push(i)
  if (rangeEnd < totalPages - 1) tokens.push('...')
  tokens.push(totalPages)

  return tokens
})

const startItem = computed(() => (props.page - 1) * props.pageSize + 1)
const endItem = computed(() => Math.min(props.page * props.pageSize, props.total))
</script>

<template>
  <div class="pagination">
    <span class="count-info">
      {{ startItem }}–{{ endItem }} / 共 {{ total }} 筆
    </span>

    <div class="page-controls">
      <button
        class="page-btn nav"
        :disabled="page <= 1"
        @click="emit('update:page', page - 1)"
      >←</button>

      <template v-for="token in pageTokens" :key="typeof token === 'number' ? token : `dots-${token}`">
        <span v-if="token === '...'" class="dots">…</span>
        <button
          v-else
          class="page-btn"
          :class="{ active: token === page }"
          @click="emit('update:page', token)"
        >{{ token }}</button>
      </template>

      <button
        class="page-btn nav"
        :disabled="page >= totalPages"
        @click="emit('update:page', page + 1)"
      >→</button>
    </div>
  </div>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 4px 4px;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.count-info {
  color: var(--muted);
}

.page-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dots {
  color: var(--muted);
  padding: 0 4px;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 6px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 12px;
  letter-spacing: 0.06em;
  transition: color 0.15s, border-color 0.15s;
}

.page-btn:hover:not(:disabled) {
  color: var(--cream);
  border-color: var(--gold-dim);
}

.page-btn.active {
  color: var(--gold);
  border-color: var(--gold);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.page-btn.nav {
  font-size: 14px;
}
</style>
