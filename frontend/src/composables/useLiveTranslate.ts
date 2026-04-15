import { ref, onUnmounted } from 'vue'
import { startTranslation, getStreamUrl } from '../api/translations'
import type { Sentence, WSMessage } from '../types/translation'

export type LiveTranslateStatus = 'idle' | 'connecting' | 'recording' | 'processing' | 'reconnecting' | 'completed' | 'error'

const MAX_RECONNECT_ATTEMPTS = 3
const INITIAL_RECONNECT_DELAY_MS = 1000

export function useLiveTranslate() {
  const sentences = ref<Sentence[]>([])
  const status = ref<LiveTranslateStatus>('idle')
  const error = ref<string | null>(null)
  const sourceLanguage = ref<string | null>(null)
  const translationId = ref<string | null>(null)

  let ws: WebSocket | null = null
  let mediaRecorder: MediaRecorder | null = null
  let audioStream: MediaStream | null = null
  let reconnectAttempts = 0
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WSMessage

      switch (message.type) {
        case 'sentence': {
          // Add new sentence or update existing one
          const existingIdx = sentences.value.findIndex(
            s => s.sentence_id === message.data.sentence_id
          )
          if (existingIdx >= 0) {
            sentences.value = [
              ...sentences.value.slice(0, existingIdx),
              message.data,
              ...sentences.value.slice(existingIdx + 1)
            ]
          } else {
            sentences.value = [...sentences.value, message.data]
          }
          break
        }
        case 'translation': {
          // Update translated text for existing sentence
          const idx = sentences.value.findIndex(
            s => s.sentence_id === message.sentence_id
          )
          if (idx >= 0) {
            sentences.value = [
              ...sentences.value.slice(0, idx),
              { ...sentences.value[idx], translated_text: message.translated_text },
              ...sentences.value.slice(idx + 1)
            ]
          }
          break
        }
        case 'status': {
          if (message.status === 'completed') {
            status.value = 'completed'
          } else if (message.status === 'interrupted') {
            status.value = 'error'
            error.value = 'Translation was interrupted'
          }
          cleanupConnection()
          break
        }
        case 'error': {
          error.value = message.message
          status.value = 'error'
          cleanupConnection()
          break
        }
      }
    } catch {
      error.value = 'Failed to parse WebSocket message'
    }
  }

  function handleError(): void {
    if (status.value === 'recording' || status.value === 'processing') {
      attemptReconnect()
    } else {
      error.value = 'WebSocket connection error'
      status.value = 'error'
      cleanupConnection()
    }
  }

  function handleClose(event: CloseEvent): void {
    // Normal closure or intentional stop
    if (event.code === 1000 || status.value === 'completed' || status.value === 'idle') {
      return
    }

    // Unexpected closure - attempt reconnect
    if (status.value === 'recording' || status.value === 'processing') {
      attemptReconnect()
    }
  }

  function attemptReconnect(): void {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      error.value = 'Connection lost. Maximum reconnection attempts exceeded.'
      status.value = 'error'
      cleanupConnection()
      return
    }

    reconnectAttempts++
    status.value = 'reconnecting'
    const delay = INITIAL_RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts - 1)

    reconnectTimer = setTimeout(() => {
      if (translationId.value) {
        connect(translationId.value)
      }
    }, delay)
  }

  function connect(id: string): void {
    const url = getStreamUrl(id)
    ws = new WebSocket(url)

    ws.onopen = () => {
      reconnectAttempts = 0
      if (status.value === 'reconnecting') {
        // Resume to previous state
        status.value = mediaRecorder?.state === 'recording' ? 'recording' : 'processing'
      }
    }

    ws.onmessage = handleMessage
    ws.onerror = handleError
    ws.onclose = handleClose
  }

  function cleanupConnection(): void {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    if (ws) {
      ws.onopen = null
      ws.onmessage = null
      ws.onerror = null
      ws.onclose = null
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close(1000)
      }
      ws = null
    }
  }

  function cleanupAudio(): void {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    mediaRecorder = null

    if (audioStream) {
      audioStream.getTracks().forEach(track => track.stop())
      audioStream = null
    }
  }

  async function start(name?: string, targetLang?: string, timesliceMs = 1000): Promise<string | null> {
    error.value = null
    sentences.value = []
    reconnectAttempts = 0
    status.value = 'connecting'

    try {
      // Start a new translation session
      const result = await startTranslation(name, targetLang)
      translationId.value = result.id

      // Connect WebSocket
      connect(result.id)

      // Get audio stream
      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Create MediaRecorder with timeslice mode for streaming
      mediaRecorder = new MediaRecorder(audioStream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws?.readyState === WebSocket.OPEN) {
          ws.send(event.data)
        }
      }

      mediaRecorder.onerror = () => {
        error.value = 'Audio recording error'
        status.value = 'error'
        stop()
      }

      // Start recording with timeslice for continuous streaming
      mediaRecorder.start(timesliceMs)
      status.value = 'recording'

      return result.id
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start translation'
      status.value = 'error'
      cleanupConnection()
      cleanupAudio()
      return null
    }
  }

  function sendAudioChunk(chunk: Blob): void {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(chunk)
    }
  }

  function stop(): void {
    // Stop audio recording
    cleanupAudio()

    // Signal server that recording has stopped
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }))
    }

    // Update status to processing if we were recording
    if (status.value === 'recording') {
      status.value = 'processing'
    }
  }

  function reset(): void {
    cleanupConnection()
    cleanupAudio()
    sentences.value = []
    status.value = 'idle'
    error.value = null
    sourceLanguage.value = null
    translationId.value = null
    reconnectAttempts = 0
  }

  // Cleanup on unmount
  onUnmounted(() => {
    reset()
  })

  return {
    // State
    sentences,
    status,
    error,
    sourceLanguage,
    translationId,
    // Computed for UI
    isConnecting: () => status.value === 'connecting',
    isRecording: () => status.value === 'recording',
    isProcessing: () => status.value === 'processing',
    isReconnecting: () => status.value === 'reconnecting',
    isCompleted: () => status.value === 'completed',
    hasError: () => status.value === 'error',
    // Methods
    start,
    stop,
    sendAudioChunk,
    reset
  }
}
