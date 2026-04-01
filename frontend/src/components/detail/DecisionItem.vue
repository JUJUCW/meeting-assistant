<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Decision } from '../../types'

const props = defineProps<{ decision: Decision; activeId: string | null }>()
const emit = defineEmits<{
  (e: 'save', id: string, body: Partial<Decision>): void
  (e: 'edit', id: string): void
  (e: 'cancel'): void
}>()

const content  = ref(props.decision.content)
const rationale = ref(props.decision.rationale ?? '')
const people   = ref((props.decision.related_people ?? []).join(', '))
const saveError = ref('')

const isEditing = ref(false)

watch(() => props.activeId, (id) => {
  isEditing.value = id === String(props.decision.id)
  if (!isEditing.value) saveError.value = ''
})

function openEdit() {
  content.value   = props.decision.content
  rationale.value = props.decision.rationale ?? ''
  people.value    = (props.decision.related_people ?? []).join(', ')
  saveError.value = ''
  emit('edit', String(props.decision.id))
}

async function save() {
  if (!content.value.trim()) { saveError.value = '內容為必填欄位'; return }
  saveError.value = ''
  emit('save', String(props.decision.id), {
    content: content.value.trim(),
    rationale: rationale.value.trim(),
    related_people: people.value.split(',').map(s => s.trim()).filter(Boolean),
  })
}
</script>

<template>
  <div class="decision-item">
    <div class="decision-display">
      <div class="decision-content">{{ decision.content }}</div>
      <div v-if="decision.rationale" class="decision-rationale">理由：{{ decision.rationale }}</div>
      <div v-if="(decision.related_people ?? []).length" class="decision-people">
        相關人員：{{ decision.related_people.join('、') }}
      </div>
      <div class="item-actions">
        <button class="btn-edit" @click="openEdit">編輯</button>
      </div>
    </div>

    <div v-if="isEditing" class="edit-form visible">
      <div class="form-group">
        <label class="form-label">決議內容</label>
        <textarea v-model="content" class="form-textarea"></textarea>
      </div>
      <div class="form-group">
        <label class="form-label">理由</label>
        <textarea v-model="rationale" class="form-textarea"></textarea>
      </div>
      <div class="form-group">
        <label class="form-label">相關人員（逗號分隔）</label>
        <input v-model="people" class="form-input" type="text" />
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
.decision-item {
  background: var(--card-bg);
  border: 1px solid rgba(212,175,55,0.15);
  padding: 18px 22px;
  margin-bottom: 12px;
}
.decision-content { font-size: 14px; letter-spacing: 0.06em; color: var(--cream); margin-bottom: 8px; line-height: 1.7; }
.decision-rationale { font-size: 12px; color: var(--muted); letter-spacing: 0.06em; line-height: 1.6; margin-bottom: 6px; }
.decision-people { font-size: 11px; color: rgba(212,175,55,0.6); letter-spacing: 0.1em; text-transform: uppercase; }
.item-actions { margin-top: 12px; display: flex; gap: 8px; }
.edit-form { display: none; margin-top: 12px; border-top: 1px solid var(--gold-dim); padding-top: 16px; }
.edit-form.visible { display: block; }
.form-group { margin-bottom: 14px; }
.form-label { display: block; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); opacity: 0.75; margin-bottom: 6px; }
.form-input, .form-textarea { width: 100%; background: rgba(212,175,55,0.04); border: 1px solid var(--gold-dim); color: var(--cream); font-family: var(--font-body); font-size: 13px; letter-spacing: 0.05em; padding: 9px 12px; outline: none; transition: border-color 0.2s; }
.form-input:focus, .form-textarea:focus { border-color: var(--gold); }
.form-textarea { resize: vertical; min-height: 72px; }
.form-buttons { display: flex; gap: 10px; }
.btn-save { font-family: var(--font-body); font-size: 12px; letter-spacing: 0.15em; text-transform: uppercase; background: rgba(212,175,55,0.12); border: 1px solid var(--gold); color: var(--gold); padding: 7px 18px; cursor: pointer; transition: background 0.2s; }
.btn-save:hover { background: rgba(212,175,55,0.22); }
.btn-cancel { font-family: var(--font-body); font-size: 12px; letter-spacing: 0.15em; text-transform: uppercase; background: transparent; border: 1px solid var(--gold-dim); color: var(--muted); padding: 7px 18px; cursor: pointer; transition: border-color 0.2s; }
.btn-cancel:hover { border-color: var(--gold); color: var(--cream); }
.form-error { color: #e88; font-size: 12px; letter-spacing: 0.06em; margin-top: 8px; }
</style>
