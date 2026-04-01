<script setup lang="ts">
import AppHeader from '../components/layout/AppHeader.vue'
import StepIndicator from '../components/upload/StepIndicator.vue'
import AudioInput from '../components/upload/AudioInput.vue'
import ProcessingStatus from '../components/upload/ProcessingStatus.vue'
import AnalysisPreview from '../components/upload/AnalysisPreview.vue'
import SummaryPanel from '../components/upload/SummaryPanel.vue'
import { useTranscription } from '../composables/useTranscription'

const { step, statusMsg, pollError, result, submitError, submit, retry, reanalyze, goToSummary, startOver } = useTranscription()
</script>

<template>
  <div>
    <AppHeader
      eyebrow="Meeting Assistant"
      title="會議助理"
      subtitle="AI-Powered Meeting Notes"
      nav-to="/history"
      nav-label="歷史紀錄 →"
    />

    <div v-if="submitError" class="submit-error">{{ submitError }}</div>

    <StepIndicator :current="step" />

    <AudioInput
      v-if="step === 1"
      @submit="submit"
    />

    <ProcessingStatus
      v-else-if="step === 2"
      :status-msg="statusMsg"
      :error="pollError"
      @retry="retry"
    />

    <AnalysisPreview
      v-else-if="step === 3 && result"
      :result="result"
      @reanalyze="reanalyze"
      @next="goToSummary"
    />

    <SummaryPanel
      v-else-if="step === 4 && result"
      :result="result"
      @start-over="startOver"
    />
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
