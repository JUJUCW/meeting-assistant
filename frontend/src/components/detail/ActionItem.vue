<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ActionItem } from '../../types'
import { priorityLabel, statusLabel } from '../../utils/format'

const props = defineProps<{ item: ActionItem; activeId: string | null }>()
const emit = defineEmits<{
  (e: 'save', id: string, body: Partial<ActionItem>): void
  (e: 'toggle', id: string): void
  (e: 'edit', id: string): void
  (e: 'cancel'): void
}>()

const content  = ref(props.item.content)
const assignee = ref(props.item.assignee ?? '')
const deadline = ref(props.item.deadline ?? '')
const priority = ref(props.item.priority ?? 'medium')
const saveError = ref('')
const isEditing = ref(false)

watch(() => props.activeId, (id) => {
  isEditing.value = id === String(props.item.id)
  if (!isEditing.value) saveError.value = ''
})

function openEdit() {
  content.value  = props.item.content
  assignee.value = props.item.assignee ?? ''
  deadline.value = props.item.deadline ?? ''
  priority.value = props.item.priority ?? 'medium'
  saveError.value = ''
  emit('edit', String(props.item.id))
}

function save() {
  if (!content.value.trim()) { saveError.value = '內容為必填欄位'; return }
  saveError.value = ''
  emit('save', String(props.item.id), {
    content: content.value.trim(),
    assignee: assignee.value.trim(),
    deadline: deadline.value || null,
    priority: priority.value,
  })
}
</script>

<template>
  <div class="action-item">
    <div class="action-display">
      <div class="action-item-header">
        <div class="action-content">{{ item.content }}</div>
        <button
          class="btn-toggle-status"
          :class="{ reopen: item.status === 'done' }"
          @click="emit('toggle', String(item.id))"
        >{{ item.status === 'done' ? '重新開啟' : '標記完成' }}</button>
      </div>
      <div class="action-meta">
        <span class="priority-badge" :class="`priority-${item.priority ?? 'medium'}`">{{ priorityLabel(item.priority ?? 'medium') }}</span>
        <span class="status-badge" :class="`status-${item.status ?? 'pending'}`">{{ statusLabel(item.status ?? 'pending') }}</span>
      </div>
      <div v-if="item.assignee" class="action-assignee">負責人：{{ item.assignee }}</div>
      <div v-if="item.deadline" class="action-deadline">截止日期：{{ item.deadline }}</div>
      <div class="item-actions">
        <button class="btn-edit" @click="openEdit">編輯</button>
      </div>
    </div>

    <div v-if="isEditing" class="edit-form visible">
      <div class="form-group">
        <label class="form-label">行動內容</label>
        <textarea v-model="content" class="form-textarea"></textarea>
      </div>
      <div class="form-group">
        <label class="form-label">負責人</label>
        <input v-model="assignee" class="form-input" type="text" />
      </div>
      <div class="form-group">
        <label class="form-label">截止日期</label>
        <input v-model="deadline" class="form-input" type="date" />
      </div>
      <div class="form-group">
        <label class="form-label">優先級</label>
        <select v-model="priority" class="form-select">
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
      </div>
      <div class="form-buttons">
        <button class="btn-save" @click="save">儲存</button>
        <button class="btn-cancel" @click="emit('cancel')">取消</button>
      </div>
      <div v-if="saveError" class="form-error">{{ saveError }}</div>
    </div>
  </div>
</template>

<style scoped>
.action-item { background: var(--card-bg); border: 1px solid rgba(212,175,55,0.15); padding: 18px 22px; margin-bottom: 12px; }
.action-item-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.action-content { font-size: 14px; letter-spacing: 0.06em; color: var(--cream); line-height: 1.7; flex: 1; }
.action-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.priority-badge, .status-badge { font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; padding: 2px 8px; border: 1px solid; }
.priority-high   { border-color: rgba(200,80,80,0.5);   color: #e07070; background: rgba(200,80,80,0.07); }
.priority-medium { border-color: rgba(200,160,60,0.5);  color: #c8a040; background: rgba(200,160,60,0.07); }
.priority-low    { border-color: rgba(100,160,100,0.5); color: #70b070; background: rgba(100,160,100,0.07); }
.status-pending  { border-color: rgba(200,160,60,0.4);  color: #c8a040; background: rgba(200,160,60,0.06); }
.status-done     { border-color: rgba(100,180,100,0.4); color: #64b464; background: rgba(100,180,100,0.06); }
.action-assignee { font-size: 12px; color: var(--muted); letter-spacing: 0.06em; }
.action-deadline { font-size: 12px; color: rgba(212,175,55,0.6); letter-spacing: 0.06em; }
.item-actions { margin-top: 12px; display: flex; gap: 8px; }
.btn-toggle-status { font-family: var(--font-body); font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; background: transparent; border: 1px solid rgba(100,180,100,0.35); color: #64b464; padding: 4px 10px; cursor: pointer; white-space: nowrap; transition: border-color 0.2s; }
.btn-toggle-status:hover { border-color: #64b464; }
.btn-toggle-status.reopen { border-color: rgba(200,160,60,0.35); color: #c8a040; }
.btn-toggle-status.reopen:hover { border-color: #c8a040; }
.edit-form { display: none; margin-top: 12px; border-top: 1px solid var(--gold-dim); padding-top: 16px; }
.edit-form.visible { display: block; }
.form-group { margin-bottom: 14px; }
.form-label { display: block; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); opacity: 0.75; margin-bottom: 6px; }
.form-input, .form-textarea, .form-select { width: 100%; background: rgba(212,175,55,0.04); border: 1px solid var(--gold-dim); color: var(--cream); font-family: var(--font-body); font-size: 13px; letter-spacing: 0.05em; padding: 9px 12px; outline: none; transition: border-color 0.2s; -webkit-appearance: none; appearance: none; }
.form-input:focus, .form-textarea:focus, .form-select:focus { border-color: var(--gold); }
.form-textarea { resize: vertical; min-height: 72px; }
.form-select option { background: #1a1a1a; }
.form-buttons { display: flex; gap: 10px; }
.btn-save { font-family: var(--font-body); font-size: 12px; letter-spacing: 0.15em; text-transform: uppercase; background: rgba(212,175,55,0.12); border: 1px solid var(--gold); color: var(--gold); padding: 7px 18px; cursor: pointer; }
.btn-cancel { font-family: var(--font-body); font-size: 12px; letter-spacing: 0.15em; text-transform: uppercase; background: transparent; border: 1px solid var(--gold-dim); color: var(--muted); padding: 7px 18px; cursor: pointer; }
.form-error { color: #e88; font-size: 12px; letter-spacing: 0.06em; margin-top: 8px; }
</style>
