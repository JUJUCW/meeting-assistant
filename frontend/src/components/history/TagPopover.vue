<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useCategories } from '../../composables/useCategories'
import type { Category } from '../../types'

const props = defineProps<{
  meetingId: string
  anchorRect: DOMRect
  initialCategoryId?: string | null
  initialTags?: string[]
}>()

const emit = defineEmits<{
  (e: 'save', payload: { categoryId: string | null; tags: string[] }): void
  (e: 'close'): void
}>()

const { categories, addCategory } = useCategories()

const selectedCategoryId = ref<string | null>(props.initialCategoryId ?? null)
const selectedTags = ref<string[]>([...(props.initialTags ?? [])])
const newTagInput = ref('')
const newCatInput = ref('')
const popoverEl = ref<HTMLDivElement>()

const style = {
  top: `${props.anchorRect.bottom + 6}px`,
  left: `${Math.min(props.anchorRect.left, window.innerWidth - 296)}px`,
}

function toggleCategory(cat: Category) {
  selectedCategoryId.value = selectedCategoryId.value === cat.id ? null : cat.id
}

function removeTag(tag: string) {
  selectedTags.value = selectedTags.value.filter(t => t !== tag)
}

function addTag(e: KeyboardEvent) {
  if (e.isComposing) return
  const val = newTagInput.value.trim()
  if (!val || selectedTags.value.includes(val)) return
  selectedTags.value = [...selectedTags.value, val]
  newTagInput.value = ''
}

async function addCat(e: KeyboardEvent) {
  if (e.isComposing) return
  const val = newCatInput.value.trim()
  if (!val) return
  try {
    const cat = await addCategory(val)
    selectedCategoryId.value = cat.id
    newCatInput.value = ''
  } catch { /* ignore */ }
}

function save() {
  emit('save', { categoryId: selectedCategoryId.value, tags: selectedTags.value })
}

function onOutsideClick(e: MouseEvent) {
  if (popoverEl.value && !popoverEl.value.contains(e.target as Node)) {
    save()
  }
}

function onEsc(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => {
  setTimeout(() => {
    document.addEventListener('click', onOutsideClick)
    document.addEventListener('keydown', onEsc)
  }, 0)
})

onUnmounted(() => {
  document.removeEventListener('click', onOutsideClick)
  document.removeEventListener('keydown', onEsc)
})
</script>

<template>
  <Teleport to="body">
    <div ref="popoverEl" class="tag-popover" :style="style">
      <div class="tag-popover-section">
        <div class="tag-popover-label">分類</div>
        <div class="tag-popover-chips">
          <span
            v-for="cat in categories"
            :key="cat.id"
            class="tag-chip category-chip"
            :class="{ 'filter-active': selectedCategoryId === cat.id }"
            @click="toggleCategory(cat)"
          >{{ cat.name }}</span>
        </div>
        <input
          v-model="newCatInput"
          class="form-input tag-popover-input"
          placeholder="新增分類後按 Enter…"
          @keydown.enter.prevent="addCat"
        />
      </div>
      <div class="tag-popover-section">
        <div class="tag-popover-label">標籤</div>
        <div class="tag-popover-chips">
          <span
            v-for="tag in selectedTags"
            :key="tag"
            class="tag-chip filter-active"
            @click="removeTag(tag)"
          >{{ tag }} ✕</span>
        </div>
        <input
          v-model="newTagInput"
          class="form-input tag-popover-input"
          placeholder="輸入新標籤後按 Enter…"
          @keydown.enter.prevent="addTag"
        />
      </div>
      <div style="text-align:right; margin-top:10px">
        <button class="btn-edit" style="font-size:12px;padding:4px 14px" @click="save">儲存</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.tag-popover {
  position: fixed;
  background: #1e1e1e;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  padding: 14px;
  width: 280px;
  z-index: 1000;
  box-shadow: 0 4px 24px rgba(0,0,0,0.5);
}
.tag-popover-label {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}
.tag-popover-section { margin-bottom: 12px; }
.tag-popover-section:last-child { margin-bottom: 0; }
.tag-popover-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.tag-popover-input { width: 100%; box-sizing: border-box; font-size: 12px; padding: 5px 8px; }
</style>
