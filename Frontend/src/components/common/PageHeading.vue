<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <section class="container py-4 py-lg-5">
    <h1 class="display-6 fw-bold mb-3">{{ title }}</h1>
    <p v-if="subtitle" class="lead text-muted mb-0">{{ subtitle }}</p>
  </section>
</template>
