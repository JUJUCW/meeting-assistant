<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AudioInput from '../components/upload/AudioInput.vue'
import { useTranscriptionJob } from '../composables/useTranscriptionJob'

const router = useRouter()
const { start } = useTranscriptionJob()
const submitError = ref('')

async function submit(file: File | Blob, filename: string, audioDuration: number) {
  submitError.value = ''
  try {
    await start(file, filename, audioDuration)
    router.push('/history')
  } catch (e) {
    submitError.value = e instanceof Error ? e.message : '送出失敗'
  }
}
</script>

<template>
  <div>
    <AppHeader
      eyebrow="Meeting Assistant"
      title="會議助理"
      subtitle="AI-Powered Meeting Notes"
      nav-to="/history"
      nav-label="歷史紀錄 →"
      nav2-to="/translate"
      nav2-label="文件翻譯 →"
    />
    <div v-if="submitError" class="submit-error">{{ submitError }}</div>
    <AudioInput @submit="submit" />
  </div>
</template>

<style scoped>
.submit-error {
  font-size: 12px;
  letter-spacing: 0.05em;
  color: #c0392b;
  margin-bottom: 16px;
  padding: 10px 14px;
  border: 1px solid rgba(192,57,43,0.3);
}
</style>
