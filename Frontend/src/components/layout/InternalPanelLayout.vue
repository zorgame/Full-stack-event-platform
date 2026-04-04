<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  links: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <section class="container py-4 py-lg-5">
    <div class="panel-hero rounded-4 p-4 p-lg-5 mb-4 shadow-sm">
      <h1 class="h2 fw-bold mb-2">{{ title }}</h1>
      <p class="text-muted mb-0">{{ subtitle }}</p>
    </div>

    <nav v-if="links.length" class="d-flex flex-wrap gap-2 mb-4">
      <RouterLink
        v-for="item in links"
        :key="item.to"
        :to="item.to"
        custom
        v-slot="{ navigate, href, isExactActive }"
      >
        <a
          :href="href"
          class="btn btn-sm fw-semibold admin-panel-link"
          :class="isExactActive ? 'admin-panel-link-active' : 'admin-panel-link-idle'"
          @click="navigate"
        >
          {{ item.label }}
        </a>
      </RouterLink>
    </nav>

    <div class="row g-3">
      <slot />
    </div>
  </section>
</template>
