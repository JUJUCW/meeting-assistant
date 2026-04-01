import { ref } from 'vue'
import { fetchCategories, createCategory, deleteCategory } from '../api/categories'
import type { Category } from '../types'

const categories = ref<Category[]>([])
let loaded = false

export function useCategories() {
  async function load() {
    if (loaded) return
    categories.value = await fetchCategories()
    loaded = true
  }

  async function addCategory(name: string): Promise<Category> {
    const cat = await createCategory(name)
    categories.value = [...categories.value, cat]
    return cat
  }

  async function removeCategory(id: string) {
    await deleteCategory(id)
    categories.value = categories.value.filter(c => c.id !== id)
  }

  return { categories, load, addCategory, removeCategory }
}
