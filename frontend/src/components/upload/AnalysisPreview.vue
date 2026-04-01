<script setup lang="ts">
import type { TranscriptionResult } from '../../types'

defineProps<{ result: TranscriptionResult }>()
defineEmits<{ (e: 'reanalyze'): void; (e: 'next'): void }>()

const priorityLabel: Record<string, string> = { low: '低', medium: '中', high: '高' }
const statusLabel: Record<string, string> = { confirmed: '確認', pending: '待定', cancelled: '取消' }
</script>

<template>
  <div class="card">
    <div class="card-title-row">
      <span class="card-step-num">III</span>
      <h2>AI 分析結果</h2>
    </div>
    <div class="card-divider"></div>

    <div v-if="!result.ollama_available" class="ollama-warn">
      ⚠ Ollama 未啟動，以下為空白分析。可啟動後重新分析。
    </div>

    <section class="section">
      <h3>決策紀錄 <span class="count">{{ result.decisions.length }}</span></h3>
      <div v-if="result.decisions.length === 0" class="empty">無決策項目</div>
      <ul v-else class="item-list">
        <li v-for="d in result.decisions" :key="d.id" class="item">
          <div class="item-content">{{ d.content }}</div>
          <div v-if="d.rationale" class="item-sub">{{ d.rationale }}</div>
          <div class="item-meta">
            <span class="badge" :class="'badge-' + d.status">{{ statusLabel[d.status] ?? d.status }}</span>
            <span v-if="d.related_people.length" class="meta-people">{{ d.related_people.join('、') }}</span>
          </div>
        </li>
      </ul>
    </section>

    <section class="section">
      <h3>待辦事項 <span class="count">{{ result.action_items.length }}</span></h3>
      <div v-if="result.action_items.length === 0" class="empty">無待辦事項</div>
      <ul v-else class="item-list">
        <li v-for="a in result.action_items" :key="a.id" class="item">
          <div class="item-content">{{ a.content }}</div>
          <div class="item-meta">
            <span class="badge" :class="'badge-priority-' + a.priority">{{ priorityLabel[a.priority] ?? a.priority }}</span>
            <span v-if="a.assignee" class="meta-people">{{ a.assignee }}</span>
            <span v-if="a.deadline" class="meta-deadline">{{ a.deadline }}</span>
          </div>
        </li>
      </ul>
    </section>

    <section class="section">
      <h3>逐字稿摘要</h3>
      <div class="transcript-preview">{{ result.transcript.slice(0, 300) }}{{ result.transcript.length > 300 ? '…' : '' }}</div>
    </section>

    <div class="actions">
      <button class="btn btn-secondary" @click="$emit('reanalyze')">重新分析</button>
      <button class="btn btn-primary" @click="$emit('next')">完成 →</button>
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
.card-divider { width: 36px; height: 1px; background: var(--gold-dim); margin-bottom: 24px; }
.ollama-warn { font-size: 12px; letter-spacing: 0.05em; color: #e67e22; background: rgba(230,126,34,0.08); border: 1px solid rgba(230,126,34,0.25); padding: 12px 16px; margin-bottom: 24px; }
.section { margin-bottom: 28px; }
h3 { font-family: var(--font-display); font-size: 13px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); font-weight: 400; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }
.count { font-family: var(--font-body); font-size: 11px; background: rgba(212,175,55,0.12); color: var(--gold); padding: 2px 8px; }
.empty { font-size: 12px; letter-spacing: 0.08em; color: rgba(136,136,136,0.5); text-transform: uppercase; padding: 10px 0; }
.item-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.item { border: 1px solid rgba(212,175,55,0.1); padding: 14px 16px; }
.item-content { font-size: 13px; letter-spacing: 0.04em; color: var(--cream); margin-bottom: 6px; }
.item-sub { font-size: 12px; letter-spacing: 0.04em; color: var(--muted); margin-bottom: 8px; }
.item-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.badge { font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; padding: 2px 8px; border: 1px solid; }
.badge-confirmed { color: #27ae60; border-color: rgba(39,174,96,0.4); }
.badge-pending { color: var(--gold); border-color: var(--gold-dim); }
.badge-cancelled { color: var(--muted); border-color: rgba(136,136,136,0.3); }
.badge-priority-high { color: #c0392b; border-color: rgba(192,57,43,0.4); }
.badge-priority-medium { color: var(--gold); border-color: var(--gold-dim); }
.badge-priority-low { color: var(--muted); border-color: rgba(136,136,136,0.3); }
.meta-people { font-size: 11px; letter-spacing: 0.08em; color: var(--muted); }
.meta-deadline { font-size: 11px; letter-spacing: 0.08em; color: rgba(212,175,55,0.6); }
.transcript-preview { font-size: 12px; letter-spacing: 0.04em; color: var(--muted); line-height: 1.7; background: rgba(255,255,255,0.02); border: 1px solid rgba(212,175,55,0.08); padding: 14px 16px; }
.actions { display: flex; gap: 14px; justify-content: flex-end; margin-top: 8px; }
.btn { padding: 13px 28px; border-radius: 0; font-family: var(--font-body); font-size: 13px; letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; transition: all 0.3s; border: none; }
.btn-primary { background: transparent; color: var(--gold); border: 1px solid var(--gold); }
.btn-primary:hover { background: var(--gold); color: #0A0A0A; box-shadow: var(--gold-glow-strong); }
.btn-secondary { background: transparent; color: var(--muted); border: 1px solid rgba(136,136,136,0.3); }
.btn-secondary:hover { color: var(--cream); border-color: rgba(242,240,228,0.4); }
</style>
