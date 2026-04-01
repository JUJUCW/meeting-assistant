<script setup lang="ts">
defineProps<{
  status: 'pending' | 'processing' | 'done' | 'error'
  estimatedSecs: number
  elapsedSecs: number
  error: string
}>()
defineEmits<{ (e: 'dismiss'): void }>()

function fmt(secs: number) {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return m > 0 ? `${m} 分 ${s} 秒` : `${s} 秒`
}
</script>

<template>
  <div class="progress-banner" :class="status">
    <div class="banner-left">
      <span class="banner-icon">{{ status === 'done' ? '✓' : status === 'error' ? '✕' : '⏳' }}</span>
      <div class="banner-text">
        <span v-if="status === 'done'" class="banner-title">轉錄完成</span>
        <span v-else-if="status === 'error'" class="banner-title">轉錄失敗</span>
        <span v-else class="banner-title">轉錄進行中</span>
        <span v-if="status === 'error'" class="banner-sub error-text">{{ error }}</span>
        <span v-else-if="status !== 'done'" class="banner-sub">
          已等待 {{ fmt(elapsedSecs) }}
          <template v-if="estimatedSecs > 0"> ／ 預計約 {{ fmt(estimatedSecs) }}</template>
        </span>
      </div>
    </div>
    <div class="banner-right">
      <button v-if="status === 'error' || status === 'done'" class="dismiss-btn" @click="$emit('dismiss')">✕</button>
    </div>
  </div>
  <div v-if="status !== 'done' && status !== 'error' && estimatedSecs > 0" class="banner-bar-track">
    <div
      class="banner-bar-fill"
      :style="{ width: Math.min(Math.round(elapsedSecs / estimatedSecs * 100), 95) + '%' }"
    ></div>
  </div>
</template>

<style scoped>
.progress-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid var(--gold-dim);
  background: rgba(212,175,55,0.04);
  margin-bottom: 0;
  gap: 12px;
}
.progress-banner.done {
  border-color: rgba(39,174,96,0.4);
  background: rgba(39,174,96,0.04);
}
.progress-banner.error {
  border-color: rgba(192,57,43,0.4);
  background: rgba(192,57,43,0.04);
}

.banner-left { display: flex; align-items: center; gap: 12px; }
.banner-icon { font-size: 16px; line-height: 1; }
.banner-text { display: flex; flex-direction: column; gap: 2px; }
.banner-title { font-size: 13px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--cream); }
.banner-sub { font-size: 11px; letter-spacing: 0.06em; color: var(--muted); font-variant-numeric: tabular-nums; }
.error-text { color: #e88; }

.done .banner-title  { color: #27ae60; }
.error .banner-title { color: #e88; }

.dismiss-btn {
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 6px;
  transition: color 0.2s;
}
.dismiss-btn:hover { color: var(--cream); }

.banner-bar-track {
  width: 100%;
  height: 2px;
  background: rgba(212,175,55,0.12);
  margin-bottom: 20px;
}
.banner-bar-fill {
  height: 100%;
  background: var(--gold);
  transition: width 1s linear;
  box-shadow: 0 0 6px rgba(212,175,55,0.4);
}
</style>
