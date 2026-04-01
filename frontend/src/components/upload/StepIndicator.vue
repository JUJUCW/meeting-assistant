<script setup lang="ts">
defineProps<{ current: number }>()
</script>

<template>
  <nav class="steps" aria-label="步驟進度">
    <template v-for="i in 4" :key="i">
      <div
        class="step-dot"
        :class="{ active: current === i, done: current > i }"
      >
        <span>{{ ['I','II','III','IV'][i-1] }}</span>
      </div>
      <div v-if="i < 4" class="step-line" :class="{ done: current > i }" aria-hidden="true" />
    </template>
  </nav>
</template>

<style scoped>
.steps { display: flex; align-items: center; margin-bottom: 44px; }

.step-dot {
  width: 42px; height: 42px;
  flex-shrink: 0;
  background: var(--card-bg);
  border: 1px solid rgba(212,175,55,0.18);
  display: flex; align-items: center; justify-content: center;
  position: relative;
  transition: border-color 0.35s, box-shadow 0.35s;
}
.step-dot::before, .step-dot::after {
  content: '';
  position: absolute;
  width: 9px; height: 9px;
  border-color: rgba(212,175,55,0.18);
  border-style: solid;
  transition: border-color 0.35s;
}
.step-dot::before { top: -1px; left: -1px;   border-width: 2px 0 0 2px; }
.step-dot::after  { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
.step-dot span { font-family: var(--font-display); font-size: 12px; color: rgba(212,175,55,0.25); transition: color 0.35s; letter-spacing: 0.04em; }

.step-dot.active { border-color: var(--gold); box-shadow: var(--gold-glow); }
.step-dot.active::before, .step-dot.active::after { border-color: var(--gold); }
.step-dot.active span { color: var(--gold); }
.step-dot.done { border-color: rgba(212,175,55,0.5); background: rgba(212,175,55,0.04); }
.step-dot.done::before, .step-dot.done::after { border-color: rgba(212,175,55,0.35); }
.step-dot.done span { color: rgba(212,175,55,0.5); }

.step-line { flex: 1; height: 1px; background: rgba(212,175,55,0.12); transition: background 0.35s; }
.step-line.done { background: rgba(212,175,55,0.45); }
</style>
