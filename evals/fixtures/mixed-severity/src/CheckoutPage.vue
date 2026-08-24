<script setup lang="ts">
import { ref } from 'vue'

const submitting = ref(false)

async function submitOrder() {
  submitting.value = true
  const response = await fetch('/api/orders', { method: 'POST' })
  if (!response.ok) {
    throw new Error('order failed')
  }
  submitting.value = false
}
</script>

<template>
  <button :disabled="submitting" @click="submitOrder">提交订单</button>
  <a href="#">支付帮助</a>
</template>
