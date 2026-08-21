<script setup lang="ts">
import { ref } from "vue";

const user = ref({ name: "", avatar: "" });

async function loadUser(id: string) {
  const response = await fetch(`/api/users/${id}`).then((item) => item.json());
  Object.assign(user.value, response.data);
}
</script>

<template>
  <p>{{ user.name }}</p>
</template>
