<script setup lang="ts">
defineProps<{ visible: boolean }>()
</script>

<template>
  <div class="server-warning" :class="{ visible }">
    無法連接伺服器，請確認後端是否運行
  </div>
</template>
