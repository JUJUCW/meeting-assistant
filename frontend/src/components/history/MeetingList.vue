<script setup lang="ts">
import MeetingCard from './MeetingCard.vue'
import type { MeetingListItem } from '../../types'

defineProps<{
  meetings: MeetingListItem[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'open', id: string): void
  (e: 'deleted', id: string): void
  (e: 'filter', type: 'category' | 'tag', value: string): void
  (e: 'updated', id: string, patch: Partial<MeetingListItem>): void
}>()
</script>

<template>
  <div v-if="isLoading" class="empty-state">載入中…</div>
  <div v-else-if="meetings.length === 0" class="empty-state">尚無會議記錄</div>
  <div v-else>
    <MeetingCard
      v-for="m in meetings"
      :key="m.id"
      :meeting="m"
      @open="emit('open', $event)"
      @deleted="emit('deleted', $event)"
      @filter="(type, value) => emit('filter', type, value)"
      @updated="(id, patch) => emit('updated', id, patch)"
    />
  </div>
</template>

<style scoped>
.empty-state {
  text-align: center;
  color: var(--muted);
  font-size: 14px;
  letter-spacing: 0.1em;
  padding: 48px 0;
}
</style>
