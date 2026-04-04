<script setup>
defineProps({
  variant: {
    type: String,
    default: 'spinner',
  },
  count: {
    type: Number,
    default: 6,
  },
})
</script>

<template>
  <div v-if="variant === 'skeleton-home'" class="skeleton-home">
    <div class="row g-3 mb-4">
      <div class="col-12 col-lg-4" v-for="idx in 3" :key="`popular-${idx}`">
        <div class="skeleton-item skeleton-pill"></div>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-12 col-md-6 col-xl-3" v-for="idx in count" :key="`card-${idx}`">
        <div class="skeleton-item skeleton-card"></div>
      </div>
    </div>
  </div>

  <div v-else-if="variant === 'skeleton-cards'" class="row g-4">
    <div class="col-12 col-md-6 col-xl-4" v-for="idx in count" :key="idx">
      <div class="skeleton-item skeleton-card"></div>
    </div>
  </div>

  <div v-else-if="variant === 'skeleton-categorias'" class="skeleton-categorias">
    <div class="row g-3">
      <div class="col-12 col-md-6" v-for="idx in count" :key="`categoria-${idx}`">
        <div class="skeleton-item skeleton-categoria"></div>
      </div>
    </div>
  </div>

  <div v-else class="d-flex align-items-center justify-content-center py-5">
    <div class="spinner-border text-primary pulse-spinner" role="status">
      <span class="visually-hidden">Cargando...</span>
    </div>
  </div>
</template>
