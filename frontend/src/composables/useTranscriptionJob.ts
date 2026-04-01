import { ref } from 'vue'
import { submitAudio, getStatus } from '../api/transcription'

const FACTOR = 5  // turbo on Apple Silicon CPU, ~5× real-time

interface JobState {
  status: 'pending' | 'processing' | 'done' | 'error'
  estimatedSecs: number
  elapsedSecs: number
  error: string
}

// Module-level singleton — survives navigation
const activeJob = ref<JobState | null>(null)
let currentJobId: string | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null
let elapsedTimer: ReturnType<typeof setInterval> | null = null

function stopTimers() {
  if (pollTimer)   { clearInterval(pollTimer);   pollTimer = null }
  if (elapsedTimer){ clearInterval(elapsedTimer); elapsedTimer = null }
}

async function poll() {
  if (!currentJobId) return
  try {
    const data = await getStatus(currentJobId)
    if (!activeJob.value) return

    if (data.status === 'done') {
      stopTimers()
      activeJob.value = { ...activeJob.value, status: 'done' }
      setTimeout(() => { activeJob.value = null }, 3000)
    } else if (data.status === 'error') {
      stopTimers()
      activeJob.value = { ...activeJob.value, status: 'error', error: '轉錄失敗' }
    } else {
      activeJob.value = { ...activeJob.value, status: data.status }
    }
  } catch {
    stopTimers()
    if (activeJob.value) {
      activeJob.value = { ...activeJob.value, status: 'error', error: '無法連線到伺服器' }
    }
  }
}

export function useTranscriptionJob() {
  async function start(file: File | Blob, filename: string, audioDuration = 0): Promise<void> {
    stopTimers()
    const res = await submitAudio(file, filename)
    currentJobId = res.job_id
    activeJob.value = {
      status: 'pending',
      estimatedSecs: audioDuration > 0 ? Math.round(audioDuration * FACTOR) : 0,
      elapsedSecs: 0,
      error: '',
    }
    pollTimer   = setInterval(poll, 2000)
    elapsedTimer = setInterval(() => {
      if (activeJob.value && activeJob.value.status !== 'done' && activeJob.value.status !== 'error') {
        activeJob.value = { ...activeJob.value, elapsedSecs: activeJob.value.elapsedSecs + 1 }
      }
    }, 1000)
  }

  function dismiss() {
    stopTimers()
    activeJob.value = null
  }

  return { activeJob, start, dismiss }
}
