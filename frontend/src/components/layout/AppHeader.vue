<script setup lang="ts">
import { useRouter } from 'vue-router'

const props = defineProps<{
  eyebrow?: string
  title: string
  subtitle?: string
  showBack?: boolean
  backTo?: string
  backLabel?: string
  navLabel?: string
  navTo?: string
  nav2Label?: string
  nav2To?: string
}>()

const router = useRouter()
</script>

<template>
  <div class="header">
    <div v-if="showBack || navTo || nav2To" class="header-nav">
      <button v-if="showBack" class="header-back-link" @click="router.push(props.backTo ?? '/')">
        {{ props.backLabel ?? '← 返回首頁' }}
      </button>
      <span v-else></span>
      <div class="header-nav-links">
        <button v-if="nav2To" class="header-nav-link" @click="router.push(nav2To!)">
          {{ nav2Label }}
        </button>
        <button v-if="navTo" class="header-nav-link" @click="router.push(navTo!)">
          {{ navLabel ?? '歷史紀錄 →' }}
        </button>
      </div>
    </div>
    <div class="header-eyebrow">{{ eyebrow ?? 'Meeting Assistant' }}</div>
    <div class="header-title">{{ title }}</div>
    <div class="header-divider">
      <div class="header-divider-line"></div>
      <div class="header-divider-diamond"></div>
      <div class="header-divider-line"></div>
    </div>
    <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
  </div>
</template>

<style scoped>
.header-nav-links {
  display: flex;
  gap: 16px;
  align-items: center;
}
</style>
