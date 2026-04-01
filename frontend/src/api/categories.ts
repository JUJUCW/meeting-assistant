import { api } from './client'
import type { Category } from '../types'

export const fetchCategories = () =>
  api.get<Category[]>('/categories')

export const createCategory = (name: string) =>
  api.post<Category>('/categories', { name })

export const deleteCategory = (id: string) =>
  api.del<void>(`/categories/${encodeURIComponent(id)}`)
