<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const saveTargetUserId = ref(String(route.params.userId))
const form = ref({ name: '', phone: '' })

watch(
  () => route.params.userId,
  async (userId) => {
    const response = await fetch(`/api/users/${String(userId)}`)
    form.value = await response.json()
  },
  { immediate: true },
)

async function saveProfile() {
  await fetch(`/api/users/${saveTargetUserId.value}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form.value),
  })
}
</script>

<template>
  <form @submit.prevent="saveProfile">
    <input v-model="form.name" />
    <input v-model="form.phone" />
    <button type="submit">保存</button>
  </form>
</template>
