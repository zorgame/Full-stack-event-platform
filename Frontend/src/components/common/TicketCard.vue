<script setup>
import { computed } from 'vue'
import { UI_TEXTS } from '../../config/constants'

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
})

const categoriesCount = computed(() => props.ticket?.categorias?.length || 0)
const formattedDate = computed(() => {
  if (!props.ticket?.fecha) return 'Fecha por confirmar'
  const date = new Date(props.ticket.fecha)
  if (Number.isNaN(date.getTime())) return 'Fecha por confirmar'
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
})

const cardCoverStyle = computed(() => {
  if (props.ticket?.imagen) {
    return {
      backgroundImage: `linear-gradient(165deg, rgba(10,11,16,0.08), rgba(10,11,16,0.24)), url(${props.ticket.imagen})`,
    }
  }

  return {
    backgroundImage:
      'linear-gradient(145deg, rgba(46,125,255,0.28), rgba(14,197,255,0.22) 45%, rgba(255,74,61,0.18) 100%)',
  }
})
</script>

<template>
  <article class="ticket-card stage-card card border-0 h-100 shadow-sm">
    <div class="stage-cover" :style="cardCoverStyle">
      <span class="stage-chip">World Cup 2026</span>
    </div>
    <div class="card-body d-flex flex-column p-3 p-lg-4">
      <p class="stage-location mb-1">
        {{ ticket.ubicacion_estadio || ticket.ubicacion || 'Ubicación por definir' }}
      </p>
      <p v-if="ticket.estadio" class="stage-date mb-2">
        Estadio {{ ticket.estadio }}
      </p>
      <h3 class="h4 stage-title fw-bold mb-2">{{ ticket.nombre }}</h3>
      <p class="text-muted mb-3 flex-grow-1">{{ ticket.descripcion || 'Acceso oficial con disponibilidad por categoria.' }}</p>
      <p class="stage-meta mb-4">{{ categoriesCount }} {{ categoriesCount === 1 ? 'categoria' : 'categorias' }} disponibles</p>

      <RouterLink class="btn btn-primary fw-semibold stretched-link position-relative stage-action" :to="`/tickets/${ticket.id}/categorias`">
        {{ UI_TEXTS.catalog.action }}
      </RouterLink>

      <p class="stage-date mb-0 mt-3">{{ formattedDate }}</p>
    </div>
  </article>
</template>
