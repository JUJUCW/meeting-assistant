<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ transcript: string }>()

const expanded = ref(false)
</script>

<template>
  <div class="section">
    <button
      class="transcript-toggle"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      逐字稿 <span class="toggle-icon">▶</span>
    </button>
    <div v-if="expanded" class="transcript-body">
      <p class="transcript-text">{{ transcript }}</p>
    </div>
  </div>
</template>

<style scoped>
.section { margin-bottom: 40px; }

.transcript-toggle {
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  padding: 0;
  color: var(--gold);
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 12px;
}
.transcript-toggle::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--gold-dim);
}
.toggle-icon {
  font-size: 10px;
  transition: transform 0.2s;
  flex-shrink: 0;
}
.transcript-toggle[aria-expanded="true"] .toggle-icon { transform: rotate(90deg); }

.transcript-body { margin-top: 16px; }
.transcript-text {
  font-size: 13px;
  line-height: 1.8;
  color: var(--muted);
  white-space: pre-wrap;
  letter-spacing: 0.02em;
}
</style>
