<script setup lang="ts">
import { ref, nextTick } from 'vue'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  inputClass?: string
  displayClass?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'save', val: string): void
}>()

const editing = ref(false)
const inputEl = ref<HTMLInputElement>()
const draft = ref('')

async function startEdit() {
  draft.value = props.modelValue
  editing.value = true
  await nextTick()
  inputEl.value?.focus()
  inputEl.value?.select()
}

function commit() {
  editing.value = false
  const val = draft.value.trim()
  if (val !== props.modelValue) {
    emit('update:modelValue', val)
    emit('save', val)
  }
}

function cancel() {
  editing.value = false
}
</script>

<template>
  <input
    v-if="editing"
    ref="inputEl"
    v-model="draft"
    :class="inputClass"
    @blur="commit"
    @keydown.enter.prevent="commit"
    @keydown.esc="cancel"
  />
  <div v-else :class="displayClass" @click="startEdit">
    <span v-if="modelValue">{{ modelValue }}</span>
    <span v-else style="color: var(--gold-dim)">{{ placeholder ?? '未命名會議' }}</span>
  </div>
</template>
