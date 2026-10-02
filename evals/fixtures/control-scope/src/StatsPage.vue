<script setup lang="ts">
import { ref } from 'vue'

const mobileStatsUrl = ref('https://example.invalid/stats/demo')
const range = ref(7)
async function copyMobileStatsUrl() {
  await navigator.clipboard.writeText(mobileStatsUrl.value)
}
</script>

<template>
  <button :disabled="!mobileStatsUrl" @click="copyMobileStatsUrl">复制手机统计地址</button>
  <label>时间范围 <input v-model="range" type="range" min="1" max="30" /></label>
</template>
