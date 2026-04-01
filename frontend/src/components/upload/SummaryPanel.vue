<script setup lang="ts">
import type { TranscriptionResult } from '../../types'

defineProps<{ result: TranscriptionResult }>()
defineEmits<{ (e: 'startOver'): void }>()

const pendingItems = (result: TranscriptionResult) =>
  result.action_items.filter(a => a.status === 'pending')
</script>

<template>
  <div class="card">
    <div class="card-title-row">
      <span class="card-step-num">IV</span>
      <h2>完成</h2>
    </div>
    <div class="card-divider"></div>

    <div class="success-row">
      <div class="check-frame">
        <span class="check">✓</span>
      </div>
      <div>
        <div class="success-title">會議記錄已儲存</div>
        <div class="success-sub">轉錄與 AI 分析已完成</div>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat">
        <div class="stat-value">{{ result.decisions.length }}</div>
        <div class="stat-label">決策項目</div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat">
        <div class="stat-value">{{ result.action_items.length }}</div>
        <div class="stat-label">待辦事項</div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat">
        <div class="stat-value">{{ pendingItems(result).length }}</div>
        <div class="stat-label">未完成</div>
      </div>
    </div>

    <div v-if="pendingItems(result).length > 0" class="pending-section">
      <h3>未完成待辦</h3>
      <ul class="pending-list">
        <li v-for="a in pendingItems(result)" :key="a.id" class="pending-item">
          <span class="pending-dot"></span>
          <div>
            <div class="pending-content">{{ a.content }}</div>
            <div class="pending-meta">
              <span v-if="a.assignee">{{ a.assignee }}</span>
              <span v-if="a.deadline" class="pending-deadline">{{ a.deadline }}</span>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <div class="actions">
      <RouterLink to="/history" class="btn btn-secondary">查看歷史紀錄</RouterLink>
      <button class="btn btn-primary" @click="$emit('startOver')">再次上傳</button>
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
.card-divider { width: 36px; height: 1px; background: var(--gold-dim); margin-bottom: 28px; }
.success-row { display: flex; align-items: center; gap: 20px; margin-bottom: 28px; }
.check-frame { width: 56px; height: 56px; border: 1px solid rgba(39,174,96,0.4); display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; }
.check-frame::before, .check-frame::after { content: ''; position: absolute; width: 10px; height: 10px; border-color: rgba(39,174,96,0.4); border-style: solid; }
.check-frame::before { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
.check-frame::after { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
.check { font-size: 22px; color: #27ae60; }
.success-title { font-family: var(--font-display); font-size: 16px; letter-spacing: 0.1em; color: var(--cream); margin-bottom: 4px; }
.success-sub { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
.stats-row { display: flex; align-items: center; gap: 0; margin-bottom: 32px; border: 1px solid rgba(212,175,55,0.1); }
.stat { flex: 1; text-align: center; padding: 18px 0; }
.stat-value { font-family: var(--font-display); font-size: 28px; color: var(--gold); margin-bottom: 4px; }
.stat-label { font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted); }
.stat-divider { width: 1px; height: 50px; background: rgba(212,175,55,0.1); }
.pending-section { margin-bottom: 28px; }
h3 { font-family: var(--font-display); font-size: 12px; letter-spacing: 0.2em; text-transform: uppercase; color: var(--gold); font-weight: 400; margin-bottom: 14px; opacity: 0.75; }
.pending-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.pending-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px 14px; border: 1px solid rgba(212,175,55,0.08); }
.pending-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--gold); opacity: 0.5; margin-top: 5px; flex-shrink: 0; }
.pending-content { font-size: 13px; letter-spacing: 0.03em; color: var(--cream); margin-bottom: 4px; }
.pending-meta { font-size: 11px; letter-spacing: 0.08em; color: var(--muted); display: flex; gap: 12px; }
.pending-deadline { color: rgba(212,175,55,0.6); }
.actions { display: flex; gap: 14px; justify-content: flex-end; }
.btn { display: inline-block; padding: 13px 28px; border-radius: 0; font-family: var(--font-body); font-size: 13px; letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; transition: all 0.3s; border: none; text-decoration: none; text-align: center; }
.btn-primary { background: transparent; color: var(--gold); border: 1px solid var(--gold); }
.btn-primary:hover { background: var(--gold); color: #0A0A0A; box-shadow: var(--gold-glow-strong); }
.btn-secondary { background: transparent; color: var(--muted); border: 1px solid rgba(136,136,136,0.3); }
.btn-secondary:hover { color: var(--cream); border-color: rgba(242,240,228,0.4); }
</style>
