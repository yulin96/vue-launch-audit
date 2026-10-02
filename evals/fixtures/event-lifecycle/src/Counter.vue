<script setup lang="ts">
import { onBeforeUnmount, onMounted, onUnmounted, ref, watch } from 'vue'
import { messages } from './messages'

const latest = ref('')
const countedByWatch = ref(0)
const countedByCallback = ref(0)
const audio = ref<HTMLAudioElement | null>(null)
const capturedAudio = new Audio('/notification.mp3')

const unsubscribe = messages.subscribe((message) => {
  latest.value = message
  countedByCallback.value += 1
})

watch(latest, () => {
  countedByWatch.value += 1
})

onMounted(() => {
  if (audio.value) audio.value.src = '/notification.mp3'
})

onBeforeUnmount(unsubscribe)
onUnmounted(() => {
  audio.value?.pause()
  audio.value?.removeAttribute('src')
  capturedAudio.pause()
  capturedAudio.removeAttribute('src')
})
</script>

<template>
  <p>Latest: {{ latest }}</p>
  <p>Watch count: {{ countedByWatch }}</p>
  <p>Callback count: {{ countedByCallback }}</p>
  <audio ref="audio" controls />
</template>
