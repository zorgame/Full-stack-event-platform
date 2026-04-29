<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppNavbar from './components/layout/AppNavbar.vue'
import AppFooter from './components/layout/AppFooter.vue'
import FloatingWhatsAppButton from './components/common/FloatingWhatsAppButton.vue'
import { transicionRuta } from './utils/animations'

const appReady = ref(false)
const route = useRoute()
let fallbackTimer = null
let finalizeTimer = null
let cleanupLoadListener = null

const mostrarBotonWhatsappFlotante = computed(() => {
  const nombreRuta = String(route.name || '')
  return nombreRuta === 'home' || nombreRuta === 'ticket-categorias'
})

function marcarAppLista() {
  if (appReady.value) return
  appReady.value = true
  document.body.classList.remove('app-shell-loading')

  if (fallbackTimer) {
    clearTimeout(fallbackTimer)
    fallbackTimer = null
  }
}

onMounted(() => {
  document.body.classList.add('app-shell-loading')
  const startedAt = Date.now()

  const finalizeBoot = () => {
    if (appReady.value) return
    const elapsed = Date.now() - startedAt
    const minVisibleMs = 420
    const waitMs = Math.max(0, minVisibleMs - elapsed)

    if (finalizeTimer) {
      clearTimeout(finalizeTimer)
    }

    finalizeTimer = window.setTimeout(() => {
      marcarAppLista()
      finalizeTimer = null
    }, waitMs)
  }

  if (document.readyState === 'complete') {
    finalizeBoot()
  } else {
    const handleWindowLoad = () => finalizeBoot()
    window.addEventListener('load', handleWindowLoad, { once: true })
    cleanupLoadListener = () => {
      window.removeEventListener('load', handleWindowLoad)
      cleanupLoadListener = null
    }
  }

  fallbackTimer = window.setTimeout(() => {
    finalizeBoot()
  }, 1800)
})

onBeforeUnmount(() => {
  if (fallbackTimer) {
    clearTimeout(fallbackTimer)
    fallbackTimer = null
  }
  if (finalizeTimer) {
    clearTimeout(finalizeTimer)
    finalizeTimer = null
  }
  if (cleanupLoadListener) {
    cleanupLoadListener()
  }
  document.body.classList.remove('app-shell-loading')
})
</script>

<template>
  <div class="d-flex flex-column min-vh-100">
    <Transition name="anim-fade-in">
      <div v-if="!appReady" class="app-boot-loader" role="status" aria-live="polite">
        <div class="app-boot-loader-content">
          <div class="app-boot-spinner" aria-hidden="true"></div>
          <p class="app-boot-label mb-0">Cargando recursos</p>
        </div>
      </div>
    </Transition>

    <div class="d-flex flex-column min-vh-100 app-shell-content" :class="{ 'app-shell-content--loading': !appReady }">
      <AppNavbar />
      <main class="flex-grow-1">
        <RouterView v-slot="{ Component }">
          <Transition v-bind="transicionRuta">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
      <FloatingWhatsAppButton v-if="mostrarBotonWhatsappFlotante" />
      <AppFooter />
    </div>
  </div>
</template>