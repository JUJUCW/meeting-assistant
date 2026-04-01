import { ref } from 'vue'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const recordedBlob = ref<Blob | null>(null)
  const duration = ref(0)
  const error = ref('')

  let mediaRecorder: MediaRecorder | null = null
  let chunks: Blob[] = []
  let timer: ReturnType<typeof setInterval> | null = null

  async function startRecording() {
    error.value = ''
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      chunks = []
      mediaRecorder = new MediaRecorder(stream)
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }
      mediaRecorder.onstop = () => {
        recordedBlob.value = new Blob(chunks, { type: 'audio/webm' })
        stream.getTracks().forEach(t => t.stop())
      }
      mediaRecorder.start()
      isRecording.value = true
      duration.value = 0
      timer = setInterval(() => { duration.value++ }, 1000)
    } catch {
      error.value = '無法存取麥克風，請確認瀏覽器已授予麥克風權限。'
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
    }
    isRecording.value = false
    if (timer) { clearInterval(timer); timer = null }
  }

  function reset() {
    stopRecording()
    recordedBlob.value = null
    duration.value = 0
    error.value = ''
  }

  function formatDuration(secs: number) {
    return `${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}`
  }

  return { isRecording, recordedBlob, duration, error, startRecording, stopRecording, reset, formatDuration }
}
