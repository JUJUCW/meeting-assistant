import { api } from './client'

export interface TranslateStatus {
  status: 'pending' | 'processing' | 'done' | 'error'
  progress: string
  total: number
  done: number
  source_lang: string | null
  error: string | null
}

export interface TranslateJob {
  id: string
  filename: string
  created_at: string
  source_lang: string | null
  status: 'done' | 'error'
  total?: number
  error?: string | null
}

export async function uploadPdf(file: File): Promise<{ job_id: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/translate/upload', { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const getTranslateStatus = (jobId: string): Promise<TranslateStatus> =>
  api.get<TranslateStatus>(`/translate/status/${jobId}`)

export const listJobs = (): Promise<{ jobs: TranslateJob[] }> =>
  api.get<{ jobs: TranslateJob[] }>('/translate/list')

export const getDownloadUrl = (jobId: string, fmt: 'pdf' | 'docx'): string =>
  `/translate/download/${jobId}/${fmt}`

export const deleteJob = (jobId: string): Promise<unknown> =>
  api.del(`/translate/${jobId}`)
