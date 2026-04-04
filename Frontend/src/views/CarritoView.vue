<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCarritoStore } from '../stores/carrito'

const router = useRouter()
const carritoStore = useCarritoStore()

carritoStore.inicializar()

const resumenCarrito = computed(() => ({
  items: carritoStore.cantidadTotal,
  subtotal: carritoStore.subtotal,
  moneda: 'USD',
}))

const carritoVacio = computed(() => resumenCarrito.value.items === 0)

function volverAlCatalogo() {
  router.push('/')
}
</script>

<template>
  <section class="carrito-vista container py-4 py-lg-5">
    <header class="carrito-encabezado mb-3">
      <p class="carrito-kicker mb-1">Compra</p>
      <h1 class="carrito-titulo mb-0">Carrito</h1>
    </header>

    <article class="carrito-panel">
      <div class="carrito-panel-titulo-row">
        <h2 class="h5 mb-0 fw-bold">
          {{ carritoVacio ? 'Tu carrito está vacío' : 'Resumen de tu carrito' }}
        </h2>
        <span class="carrito-badge">{{ resumenCarrito.items }} items</span>
      </div>

      <p v-if="carritoVacio" class="text-muted mb-3">
        Aún no has agregado entradas. Regresa al catálogo y selecciona una categoría para comenzar tu compra.
      </p>

      <p v-else class="text-muted mb-3">
        Pronto podrás revisar categorías, cantidades y crear tu pedido desde aquí.
      </p>

      <div class="carrito-resumen mb-3">
        <p class="mb-1">Subtotal</p>
        <strong>{{ resumenCarrito.subtotal.toFixed(2) }} {{ resumenCarrito.moneda }}</strong>
      </div>

      <button type="button" class="btn btn-primary fw-semibold" @click="volverAlCatalogo">
        Ver tickets
      </button>
    </article>
  </section>
</template>
