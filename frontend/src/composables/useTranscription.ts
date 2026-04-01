import { ref, onUnmounted } from 'vue'
import { submitAudio, getStatus, getResult } from '../api/transcription'
import type { TranscriptionResult } from '../types'

export function useTranscription() {
  const step = ref(1)
  const jobId = ref<string | null>(null)
  const statusMsg = ref('初始化中...')
  const pollError = ref('')
  const result = ref<TranscriptionResult | null>(null)
  const submitError = ref('')

  let pollTimer: ReturnType<typeof setInterval> | null = null

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  }

  onUnmounted(stopPolling)

  async function submit(file: File | Blob, filename?: string) {
    submitError.value = ''
    try {
      const res = await submitAudio(file, filename)
      jobId.value = res.job_id
      step.value = 2
      startPolling()
    } catch (e) {
      submitError.value = e instanceof Error ? e.message : '送出失敗'
    }
  }

  function startPolling() {
    statusMsg.value = '轉錄中，請稍候...'
    pollError.value = ''
    pollTimer = setInterval(poll, 2000)
  }

  async function poll() {
    try {
      const data = await getStatus(jobId.value!)
      if (data.status === 'done') {
        stopPolling()
        await loadResult()
      } else if (data.status === 'error') {
        stopPolling()
        pollError.value = data.message ?? '轉錄失敗'
      } else {
        const labels: Record<string, string> = { pending: '等待處理...', processing: '轉錄中，請稍候...' }
        statusMsg.value = labels[data.status] ?? '處理中...'
      }
    } catch {
      stopPolling()
      pollError.value = '無法連線到伺服器'
    }
  }

  async function loadResult() {
    try {
      result.value = await getResult(jobId.value!)
      step.value = 3
    } catch {
      pollError.value = '無法取得轉錄結果'
    }
  }

  async function reanalyze() {
    if (!jobId.value) return
    try {
      result.value = await getResult(jobId.value)
    } catch { /* ignore */ }
  }

  function retry() {
    step.value = 1
    pollError.value = ''
    statusMsg.value = '初始化中...'
  }

  function goToSummary() { step.value = 4 }

  function startOver() {
    stopPolling()
    step.value = 1
    jobId.value = null
    result.value = null
    statusMsg.value = '初始化中...'
    pollError.value = ''
    submitError.value = ''
  }

  return { step, statusMsg, pollError, result, submitError, submit, retry, reanalyze, goToSummary, startOver }
}
