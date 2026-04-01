<script setup lang="ts">
defineProps<{ statusMsg: string; error: string }>()
defineEmits<{ (e: 'retry'): void }>()
</script>

<template>
  <div class="card">
    <div class="card-title-row">
      <span class="card-step-num">II</span>
      <h2>語音轉錄</h2>
    </div>
    <div class="card-divider"></div>
    <p>本地 Whisper 模型處理中，請稍候</p>
    <div class="progress-center">
      <div class="spinner-frame">
        <div class="spinner">{{ error ? '❌' : '⏳' }}</div>
      </div>
      <div class="progress-status">{{ error ? '發生錯誤' : statusMsg }}</div>
      <div v-if="error" class="error-msg">{{ error }}</div>
      <button v-if="error" class="btn btn-secondary retry-btn" @click="$emit('retry')">重試</button>
    </div>
  </div>
</template>

<style scoped>
.card { background: var(--card-bg); border: 1px solid var(--gold-dim); padding: 36px; position: relative; }
.card::before, .card::after { content: ''; position: absolute; width: 18px; height: 18px; border-color: var(--gold); border-style: solid; }
.card::before { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
.card::after  { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
.card-title-row { display: flex; align-items: baseline; gap: 14px; margin-bottom: 10px; }
.card-step-num { font-family: var(--font-display); font-size: 11px; color: var(--gold); letter-spacing: 0.2em; opacity: 0.65; }
h2 { font-family: var(--font-display); font-size: 20px; font-weight: 400; color: var(--cream); text-transform: uppercase; letter-spacing: 0.12em; }
.card-divider { width: 36px; height: 1px; background: var(--gold-dim); margin-bottom: 18px; }
p { font-size: 13px; letter-spacing: 0.08em; color: var(--muted); text-transform: uppercase; margin-bottom: 32px; }
.progress-center { text-align: center; padding: 36px 0; }
.spinner-frame { width: 68px; height: 68px; border: 1px solid var(--gold-dim); display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; position: relative; }
.spinner-frame::before, .spinner-frame::after { content: ''; position: absolute; width: 12px; height: 12px; border-color: var(--gold); border-style: solid; }
.spinner-frame::before { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
.spinner-frame::after { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
.spinner { font-size: 28px; line-height: 1; }
.progress-status { font-family: var(--font-body); font-size: 13px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--muted); }
.error-msg { font-size: 12px; letter-spacing: 0.05em; color: #c0392b; margin-top: 18px; }
.retry-btn { margin-top: 22px; }
.btn { padding: 13px 28px; border-radius: 0; font-family: var(--font-body); font-size: 13px; letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; transition: all 0.3s; border: none; }
.btn-secondary { background: transparent; color: var(--muted); border: 1px solid rgba(136,136,136,0.3); }
.btn-secondary:hover { color: var(--cream); border-color: rgba(242,240,228,0.4); }
</style>
