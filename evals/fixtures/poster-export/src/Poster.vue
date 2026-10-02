<script setup lang="ts">
import { ref } from 'vue'
import html2canvas from 'html2canvas'

const nickname = ref('小明 ABC')
const poster = ref<HTMLElement | null>(null)

async function exportPoster() {
  if (!poster.value) return
  await document.fonts.ready
  const canvas = await html2canvas(poster.value)
  canvas.toBlob((blob) => {
    if (!blob) throw new Error('PNG encoding returned no image')
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'poster.png'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }, 'image/png')
}
</script>

<template>
  <input v-model="nickname" />
  <div ref="poster" class="poster">
    <div class="nickname">{{ nickname }}</div>
  </div>
  <button @click="exportPoster">导出海报</button>
</template>

<style scoped>
.poster { width: 400px; height: 600px; background: #fff; }
.nickname { display: flex; align-items: center; justify-content: center; height: 80px; }
</style>
