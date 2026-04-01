<script setup lang="ts">
import { ref } from 'vue'
import DecisionItem from './DecisionItem.vue'
import type { Decision } from '../../types'

defineProps<{ decisions: Decision[] }>()
const emit = defineEmits<{
  (e: 'save', id: string, body: Partial<Decision>): void
  (e: 'add', body: Partial<Decision>): void
}>()

const activeId   = ref<string | null>(null)
const showAdd    = ref(false)
const addContent = ref('')
const addRationale = ref('')
const addPeople  = ref('')
const addError   = ref('')

function openEdit(id: string) { activeId.value = id; showAdd.value = false }
function cancelEdit() { activeId.value = null }

async function onSave(id: string, body: Partial<Decision>) {
  emit('save', id, body)
  activeId.value = null
}

function openAdd() { showAdd.value = true; activeId.value = null; addContent.value = ''; addRationale.value = ''; addPeople.value = ''; addError.value = '' }

function submitAdd() {
  if (!addContent.value.trim()) { addError.value = '內容為必填欄位'; return }
  emit('add', {
    content: addContent.value.trim(),
    rationale: addRationale.value.trim(),
    related_people: addPeople.value.split(',').map(s => s.trim()).filter(Boolean),
  })
  showAdd.value = false
}
</script>

<template>
  <div class="section">
    <div class="section-heading">決議事項</div>

    <div v-if="!decisions.length" class="empty-text">無決議事項</div>

    <DecisionItem
      v-for="d in decisions"
      :key="d.id"
      :decision="d"
      :active-id="activeId"
      @edit="openEdit"
      @cancel="cancelEdit"
      @save="onSave"
    />

    <div v-if="showAdd" class="decision-item">
      <div class="edit-form visible">
        <div class="form-group">
          <label class="form-label">決議內容（必填）</label>
          <textarea v-model="addContent" class="form-textarea"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">依據</label>
          <input v-model="addRationale" class="form-input" type="text" />
        </div>
        <div class="form-group">
          <label class="form-label">相關人員（逗號分隔）</label>
          <input v-model="addPeople" class="form-input" type="text" />
        </div>
        <div class="form-buttons">
          <button class="btn-save" @click="submitAdd">儲存</button>
          <button class="btn-cancel" @click="showAdd = false">取消</button>
        </div>
        <div v-if="addError" class="form-error">{{ addError }}</div>
      </div>
    </div>

    <button class="btn-edit add-btn" @click="openAdd">＋ 新增決議</button>
  </div>
</template>

<style scoped>
.section { margin-bottom: 40px; }
.section-heading { font-family: var(--font-display); font-size: 14px; letter-spacing: 0.22em; text-transform: uppercase; color: var(--gold); margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.section-heading::after { content: ''; flex: 1; height: 1px; background: var(--gold-dim); }
.empty-text { text-align: center; color: var(--muted); font-size: 13px; letter-spacing: 0.12em; padding: 20px 0; }
.add-btn { margin-top: 12px; display: block; }
.decision-item { background: var(--card-bg); border: 1px solid rgba(212,175,55,0.15); padding: 18px 22px; margin-bottom: 12px; }
.edit-form { display: none; margin-top: 12px; }
.edit-form.visible { display: block; }
.form-group { margin-bottom: 14px; }
.form-label { display: block; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); opacity: 0.75; margin-bottom: 6px; }
.form-input, .form-textarea { width: 100%; background: rgba(212,175,55,0.04); border: 1px solid var(--gold-dim); color: var(--cream); font-family: var(--font-body); font-size: 13px; letter-spacing: 0.05em; padding: 9px 12px; outline: none; transition: border-color 0.2s; }
.form-input:focus, .form-textarea:focus { border-color: var(--gold); }
.form-textarea { resize: vertical; min-height: 72px; }
.form-buttons { display: flex; gap: 10px; }
.btn-save { font-family: var(--font-body); font-size: 12px; letter-spacing: 0.15em; text-transform: uppercase; background: rgba(212,175,55,0.12); border: 1px solid var(--gold); color: var(--gold); padding: 7px 18px; cursor: pointer; }
.btn-cancel { font-family: var(--font-body); font-size: 12px; letter-spacing: 0.15em; text-transform: uppercase; background: transparent; border: 1px solid var(--gold-dim); color: var(--muted); padding: 7px 18px; cursor: pointer; }
.form-error { color: #e88; font-size: 12px; letter-spacing: 0.06em; margin-top: 8px; }
</style>
