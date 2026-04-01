<script setup lang="ts">
import { ref } from 'vue'
import ActionItem from './ActionItem.vue'
import type { ActionItem as ActionItemType } from '../../types'

defineProps<{ items: ActionItemType[] }>()
const emit = defineEmits<{
  (e: 'save', id: string, body: Partial<ActionItemType>): void
  (e: 'toggle', id: string): void
  (e: 'add', body: Partial<ActionItemType>): void
}>()

const activeId   = ref<string | null>(null)
const showAdd    = ref(false)
const addContent  = ref('')
const addAssignee = ref('')
const addDeadline = ref('')
const addPriority = ref<'high' | 'medium' | 'low'>('medium')
const addError    = ref('')

function openEdit(id: string) { activeId.value = id; showAdd.value = false }
function cancelEdit() { activeId.value = null }

function onSave(id: string, body: Partial<ActionItemType>) {
  emit('save', id, body)
  activeId.value = null
}

function openAdd() { showAdd.value = true; activeId.value = null; addContent.value = ''; addAssignee.value = ''; addDeadline.value = ''; addPriority.value = 'medium'; addError.value = '' }

function submitAdd() {
  if (!addContent.value.trim()) { addError.value = '內容為必填欄位'; return }
  emit('add', {
    content: addContent.value.trim(),
    assignee: addAssignee.value.trim(),
    deadline: addDeadline.value || null,
    priority: addPriority.value,
  })
  showAdd.value = false
}
</script>

<template>
  <div class="section">
    <div class="section-heading">行動項目</div>

    <div v-if="!items.length" class="empty-text">無行動項目</div>

    <ActionItem
      v-for="a in items"
      :key="a.id"
      :item="a"
      :active-id="activeId"
      @edit="openEdit"
      @cancel="cancelEdit"
      @save="onSave"
      @toggle="emit('toggle', $event)"
    />

    <div v-if="showAdd" class="add-form-wrapper">
      <div class="edit-form visible">
        <div class="form-group">
          <label class="form-label">行動內容（必填）</label>
          <textarea v-model="addContent" class="form-textarea"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">負責人</label>
          <input v-model="addAssignee" class="form-input" type="text" />
        </div>
        <div class="form-group">
          <label class="form-label">截止日期</label>
          <input v-model="addDeadline" class="form-input" type="date" />
        </div>
        <div class="form-group">
          <label class="form-label">優先級</label>
          <select v-model="addPriority" class="form-select">
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
        </div>
        <div class="form-buttons">
          <button class="btn-save" @click="submitAdd">儲存</button>
          <button class="btn-cancel" @click="showAdd = false">取消</button>
        </div>
        <div v-if="addError" class="form-error">{{ addError }}</div>
      </div>
    </div>

    <button class="btn-edit add-btn" @click="openAdd">＋ 新增待辦事項</button>
  </div>
</template>

<style scoped>
.section { margin-bottom: 40px; }
.section-heading { font-family: var(--font-display); font-size: 14px; letter-spacing: 0.22em; text-transform: uppercase; color: var(--gold); margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.section-heading::after { content: ''; flex: 1; height: 1px; background: var(--gold-dim); }
.empty-text { text-align: center; color: var(--muted); font-size: 13px; letter-spacing: 0.12em; padding: 20px 0; }
.add-btn { margin-top: 12px; display: block; }
.add-form-wrapper { background: var(--card-bg); border: 1px solid rgba(212,175,55,0.15); padding: 18px 22px; margin-bottom: 12px; }
.edit-form { display: none; }
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
