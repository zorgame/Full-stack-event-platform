<script setup>
import { computed } from 'vue'
import { UI_TEXTS } from '../../config/constants'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({
      tickets: 0,
      categorias: 0,
      unidades: 0,
    }),
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
})

function formatCompactNumber(value) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed < 0) return '0'
  return parsed.toLocaleString('es-CO')
}

const heroOperationalSummary = computed(() => {
  if (props.isLoading) {
    return 'Estamos actualizando disponibilidad y mejores opciones para tu compra.'
  }

  return `Descubre ${formatCompactNumber(props.stats.tickets)} partidos en venta, compara ${formatCompactNumber(props.stats.categorias)} categorías y elige entre ${formatCompactNumber(props.stats.unidades)} entradas disponibles hoy.`
})
</script>

<template>
  <header class="hero-banner py-3 py-lg-4">
    <div class="container py-lg-3">
      <div class="row align-items-center g-4 hero-grid">
        <div class="col-12 col-lg-8 order-2 order-lg-1 hero-copy">
          <p class="hero-kicker mb-2">Entradas FIFA World Cup 2026</p>
          <h1 class="display-4 fw-bold text-white lh-sm mb-2">{{ UI_TEXTS.hero.title }}</h1>
          <p class="hero-tagline mb-3">Compara categorías, revisa disponibilidad real y compra con confianza.</p>
          <p class="lead hero-subtitle mb-3">
            Encuentra la ubicación ideal para tu presupuesto, confirma en minutos y prepárate para vivir el
            partido sin complicaciones.
          </p>
          <p class="hero-ops-meta mb-0">{{ heroOperationalSummary }}</p>
        </div>

        <div class="col-12 col-lg-4 order-1 order-lg-2 d-flex justify-content-center justify-content-lg-end hero-mark-col">
          <div class="hero-mark shadow-lg">
            <p class="hero-mark-label mb-0">FIFA World Cup</p>
            <p class="hero-mark-year mb-0">2026</p>
            <div class="hero-mark-divider" aria-hidden="true"></div>
            <p class="hero-mark-host mb-0">USA • MEX • CAN</p>
            <p class="hero-mark-subtitle mb-0">Compra segura</p>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
