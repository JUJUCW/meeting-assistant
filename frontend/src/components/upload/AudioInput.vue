<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAudioRecorder } from '../../composables/useAudioRecorder'

const emit = defineEmits<{ (e: 'submit', file: File | Blob, filename: string, audioDuration: number): void }>()

const { isRecording, recordedBlob, duration, error: recError, startRecording, stopRecording, reset: resetRecorder, formatDuration } = useAudioRecorder()

const selectedFile = ref<File | null>(null)
const audioDuration = ref(0)
const fileError = ref('')
const serverError = ref(false)

const MAX_SIZE = 200 * 1024 * 1024

const canSubmit = computed(() => !!(selectedFile.value || recordedBlob.value))

async function checkServer() {
  try {
    const r = await fetch('/health')
    if (!r.ok) throw new Error()
  } catch {
    serverError.value = true
  }
}
checkServer()

function getAudioDuration(file: File): Promise<number> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file)
    const audio = new Audio(url)
    const cleanup = () => URL.revokeObjectURL(url)
    audio.addEventListener('loadedmetadata', () => { cleanup(); resolve(Math.round(audio.duration)) })
    audio.addEventListener('error', () => { cleanup(); resolve(0) })
    setTimeout(() => { cleanup(); resolve(0) }, 5000)
  })
}

async function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0] ?? null
  fileError.value = ''
  audioDuration.value = 0
  if (file && file.size > MAX_SIZE) {
    fileError.value = '檔案過大，上限為 200 MB。'
    selectedFile.value = null
    return
  }
  selectedFile.value = file
  resetRecorder()
  if (file) audioDuration.value = await getAudioDuration(file)
}

function toggleRecord() {
  if (isRecording.value) {
    stopRecording()
  } else {
    selectedFile.value = null
    startRecording()
  }
}

function submit() {
  const audio = selectedFile.value || recordedBlob.value
  if (!audio) return
  const filename = selectedFile.value ? selectedFile.value.name : 'recording.webm'
  const dur = selectedFile.value ? audioDuration.value : duration.value
  emit('submit', audio, filename, dur)
}
</script>

<template>
  <div class="card">
    <div class="card-title-row">
      <span class="card-step-num">I</span>
      <h2>音訊輸入</h2>
    </div>
    <div class="card-divider"></div>
    <p>上傳音檔或即時錄音以開始轉錄</p>

    <div v-if="serverError" class="error-msg" style="margin-bottom:20px">
      ⚠ 無法連線到本地伺服器，請先執行：<code>uvicorn server:app --reload</code>
    </div>

    <div class="field">
      <label class="field-label" for="fileInput">上傳音檔</label>
      <input type="file" id="fileInput" accept=".mp3,.wav,.m4a,.ogg,.flac,.webm" @change="onFileChange" />
      <div v-if="fileError" class="error-msg">{{ fileError }}</div>
    </div>

    <div class="or-divider">或</div>

    <div class="field">
      <label class="field-label">即時錄音</label>
      <div class="record-row">
        <button
          class="btn btn-secondary"
          :class="{ 'btn-recording': isRecording }"
          @click="toggleRecord"
        >{{ isRecording ? '■ 停止錄音' : '● 開始錄音' }}</button>
        <div v-if="isRecording" class="rec-dot"></div>
        <span v-if="isRecording" class="rec-timer">{{ formatDuration(duration) }}</span>
        <span v-if="recordedBlob && !isRecording" class="rec-done">錄音完成 ✓</span>
      </div>
      <div v-if="recError" class="error-msg">{{ recError }}</div>
    </div>

    <button class="btn btn-primary" :disabled="!canSubmit" @click="submit">送出轉錄</button>
  </div>
</template>

<style scoped>
.card { background: var(--card-bg); border: 1px solid var(--gold-dim); padding: 36px; position: relative; }
.card::before, .card::after { content: ''; position: absolute; width: 18px; height: 18px; border-color: var(--gold); border-style: solid; }
.card::before { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
.card::after  { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
.card-title-row { display: flex; align-items: baseline; gap: 14px; margin-bottom: 10px; }
.card-step-num { font-family: var(--font-display); font-size: 11px; color: var(--gold); letter-spacing: 0.2em; opacity: 0.65; }
h2 { font-family: var(--font-display); font-size: 20px; font-weight: 400; color: var(--cream); text-transform: uppercase; letter-spacing: 0.12em; }
.card-divider { width: 36px; height: 1px; background: var(--gold-dim); margin-bottom: 18px; }
p { font-size: 13px; letter-spacing: 0.08em; color: var(--muted); text-transform: uppercase; margin-bottom: 32px; }
.field { margin-bottom: 28px; }
.field-label { display: block; font-size: 12px; letter-spacing: 0.2em; text-transform: uppercase; color: var(--gold); margin-bottom: 12px; opacity: 0.75; }
input[type="file"] { width: 100%; font-family: var(--font-body); font-size: 12px; letter-spacing: 0.05em; color: var(--muted); background: transparent; border: none; border-bottom: 1px solid var(--gold-dim); padding: 10px 0; cursor: pointer; transition: border-color 0.3s; }
input[type="file"]:hover { border-bottom-color: rgba(212,175,55,0.6); }
input[type="file"]::file-selector-button { background: transparent; color: var(--gold); border: 1px solid var(--gold-dim); padding: 6px 14px; font-family: var(--font-body); font-size: 11px; letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; margin-right: 14px; transition: all 0.3s; border-radius: 0; }
input[type="file"]::file-selector-button:hover { background: var(--gold); color: #0A0A0A; border-color: var(--gold); }
.or-divider { display: flex; align-items: center; gap: 18px; margin: 28px 0; font-size: 12px; letter-spacing: 0.25em; text-transform: uppercase; color: rgba(136,136,136,0.4); }
.or-divider::before, .or-divider::after { content: ''; flex: 1; height: 1px; background: rgba(212,175,55,0.1); }
.record-row { display: flex; gap: 14px; align-items: center; }
.rec-done { font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--gold); }
@keyframes pulse-dot { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.3; transform: scale(0.7); } }
.rec-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #c0392b; animation: pulse-dot 1s ease-in-out infinite; flex-shrink: 0; }
.rec-timer { font-family: var(--font-body); font-size: 13px; letter-spacing: 0.12em; color: #c0392b; min-width: 44px; }
.btn { padding: 13px 28px; border-radius: 0; font-family: var(--font-body); font-size: 13px; letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; transition: all 0.3s ease; border: none; }
.btn-primary { background: transparent; color: var(--gold); border: 1px solid var(--gold); }
.btn-primary:hover { background: var(--gold); color: #0A0A0A; box-shadow: var(--gold-glow-strong); }
.btn-primary:disabled { background: transparent; color: rgba(212,175,55,0.2); border-color: rgba(212,175,55,0.2); cursor: not-allowed; }
.btn-secondary { background: transparent; color: var(--muted); border: 1px solid rgba(136,136,136,0.3); }
.btn-secondary:hover { color: var(--cream); border-color: rgba(242,240,228,0.4); }
.error-msg { font-size: 12px; letter-spacing: 0.05em; color: #c0392b; margin-top: 10px; }
code { font-family: monospace; font-size: 11px; background: rgba(212,175,55,0.08); padding: 2px 7px; color: var(--gold); }
</style>
