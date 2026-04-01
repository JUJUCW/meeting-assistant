<script setup lang="ts">
defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: string): void }>()
</script>

<template>
  <div class="search-bar">
    <input
      class="search-input"
      type="text"
      placeholder="搜尋逐字稿、決議、待辦…"
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
  </div>
</template>

<style scoped>
.search-bar { margin-bottom: 28px; }
.search-input {
  width: 100%;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--gold-dim);
  color: var(--cream);
  font-family: var(--font-body);
  font-size: 14px;
  padding: 10px 16px;
  outline: none;
  letter-spacing: 0.05em;
  transition: border-color 0.2s;
}
.search-input:focus { border-color: var(--gold); }
.search-input::placeholder { color: var(--muted); }
</style>
