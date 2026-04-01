import { api } from './client'
import type { TranscriptionStatus, TranscriptionResult } from '../types'

export async function submitAudio(file: File | Blob, filename = 'audio.wav'): Promise<{ job_id: string }> {
  const form = new FormData()
  form.append('file', file, filename)
  const res = await fetch('/transcribe', { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const getStatus = (jobId: string) =>
  api.get<TranscriptionStatus>(`/status/${encodeURIComponent(jobId)}`)

export const getResult = (jobId: string) =>
  api.get<TranscriptionResult>(`/result/${encodeURIComponent(jobId)}`)
