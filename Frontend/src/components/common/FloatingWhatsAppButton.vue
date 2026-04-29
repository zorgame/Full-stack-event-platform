<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { CONTACT_INFO } from '../../config/constants'
import { construirEnlaceWhatsapp } from '../../utils/whatsapp'

const MENSAJE_WA = 'Hola, necesito ayuda con mis tickets.'

const whatsappNumber = computed(() => String(CONTACT_INFO.whatsappDigits || '').replace(/\D/g, ''))

const whatsappHref = computed(() => {
  const numero = whatsappNumber.value
  if (!numero) return ''

  const enlaceConfigurado = construirEnlaceWhatsapp(numero, MENSAJE_WA)
  if (enlaceConfigurado) return enlaceConfigurado

  return `https://wa.me/${numero}?text=${encodeURIComponent(MENSAJE_WA)}`
})

const ocultarPorFooter = ref(false)
const ocultarPorHeader = ref(true)
let footerObserver = null
let observerAnimationFrameId = 0

function actualizarVisibilidadPorHeader() {
  if (typeof window === 'undefined') {
    return
  }

  const navbar = document.querySelector('nav.app-navbar')
  const navbarHeight = Math.max(56, Number(navbar?.getBoundingClientRect().height || 0))
  const scrollTop = Math.max(0, Number(window.scrollY || window.pageYOffset || 0))
  const umbralAparicion = navbarHeight + 8

  ocultarPorHeader.value = scrollTop <= umbralAparicion
}

function conectarObserverFooter() {
  if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') {
    return
  }

  const footer = document.querySelector('footer.app-footer') || document.querySelector('footer')
  if (!footer) {
    observerAnimationFrameId = window.requestAnimationFrame(conectarObserverFooter)
    return
  }

  footerObserver = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      ocultarPorFooter.value = Boolean(entry?.isIntersecting && entry.intersectionRatio >= 0.5)
    },
    {
      threshold: [0, 0.5, 1],
    },
  )

  footerObserver.observe(footer)
}

onMounted(() => {
  ocultarPorFooter.value = false
  ocultarPorHeader.value = true
  conectarObserverFooter()
  actualizarVisibilidadPorHeader()
  window.addEventListener('scroll', actualizarVisibilidadPorHeader, { passive: true })
  window.addEventListener('resize', actualizarVisibilidadPorHeader)
})

onBeforeUnmount(() => {
  if (observerAnimationFrameId) {
    cancelAnimationFrame(observerAnimationFrameId)
    observerAnimationFrameId = 0
  }

  if (footerObserver) {
    footerObserver.disconnect()
    footerObserver = null
  }

  window.removeEventListener('scroll', actualizarVisibilidadPorHeader)
  window.removeEventListener('resize', actualizarVisibilidadPorHeader)
})
</script>

<template>
  <a
    v-if="whatsappHref"
    class="whatsapp-fab"
    :class="{ 'whatsapp-fab--hidden': ocultarPorFooter || ocultarPorHeader }"
    :href="whatsappHref"
    target="_blank"
    rel="noopener noreferrer"
    aria-label="Abrir soporte por WhatsApp"
    title="Soporte"
  >
    <span class="whatsapp-fab-icono-wrap" aria-hidden="true">
      <span class="whatsapp-fab-icono">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M12 4.4C7.8 4.4 4.4 7.7 4.4 11.8C4.4 13.3 4.9 14.7 5.7 15.9L4.8 19.8L8.8 19C9.9 19.7 11.2 20 12.5 20C16.7 20 20 16.7 20 12.6C20 8.5 16.2 4.4 12 4.4Z"
            stroke="currentColor"
            stroke-width="1.55"
          />
          <path
            d="M9.2 9.7C9.4 9.2 9.6 9.1 9.9 9.1H10.4C10.6 9.1 10.7 9.2 10.8 9.4L11.5 11.1C11.6 11.3 11.6 11.4 11.4 11.6L10.9 12.3C10.8 12.4 10.9 12.6 11 12.7C11.5 13.3 12 13.8 12.7 14.2C12.8 14.3 13 14.3 13.2 14.2L13.8 13.7C14 13.6 14.2 13.6 14.4 13.7L16 14.4C16.2 14.5 16.3 14.7 16.3 14.9V15.4C16.3 15.7 16.2 15.9 15.8 16.1C15.3 16.3 14.8 16.3 14.3 16.2C13.4 15.9 12.5 15.3 11.8 14.5C11 13.8 10.5 13 10.1 12.1C10 11.6 10 11.1 10.2 10.6"
            fill="currentColor"
          />
        </svg>
      </span>
    </span>
    <span class="whatsapp-fab-copy">
      <span class="whatsapp-fab-texto">Soporte</span>
      <span class="whatsapp-fab-subtexto">Respuesta rapida</span>
    </span>
    <span class="whatsapp-fab-status" aria-hidden="true"></span>
  </a>
</template>

<style scoped>
.whatsapp-fab {
  position: fixed;
  right: calc(1.2rem + env(safe-area-inset-right));
  bottom: calc(1rem + env(safe-area-inset-bottom));
  z-index: 1040;
  display: inline-flex;
  align-items: center;
  gap: 0.62rem;
  min-height: 3.8rem;
  padding: 0.7rem 1.08rem 0.7rem 0.72rem;
  border-radius: 999px;
  border: 1px solid rgba(170, 255, 204, 0.58);
  background: linear-gradient(132deg, rgba(10, 161, 72, 0.98) 0%, rgba(19, 197, 93, 0.98) 58%, rgba(55, 227, 127, 0.98) 100%);
  color: #ffffff;
  text-decoration: none;
  box-shadow: 0 16px 30px rgba(12, 93, 42, 0.34);
  overflow: hidden;
  isolation: isolate;
  transform: translateY(0);
  transform-origin: center;
  will-change: transform, box-shadow, opacity;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease, opacity 0.2s ease;
  animation: whatsapp-fab-float 2.8s ease-in-out infinite, whatsapp-fab-glow 3.9s ease-in-out infinite;
}

.whatsapp-fab::before {
  content: '';
  position: absolute;
  top: -125%;
  left: -48%;
  width: 42%;
  height: 320%;
  background: linear-gradient(
    115deg,
    transparent 0%,
    rgba(255, 255, 255, 0.07) 42%,
    rgba(255, 255, 255, 0.42) 50%,
    rgba(255, 255, 255, 0.1) 58%,
    transparent 100%
  );
  transform: rotate(18deg);
  pointer-events: none;
  animation: whatsapp-fab-shine 4.8s ease-in-out infinite;
}

.whatsapp-fab:hover {
  animation-play-state: paused;
  transform: translateY(-4px) scale(1.04);
  box-shadow: 0 20px 34px rgba(12, 93, 42, 0.42);
  filter: saturate(1.1);
}

.whatsapp-fab:active {
  transform: translateY(-1px) scale(0.99);
}

.whatsapp-fab-icono-wrap {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.07));
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.25), 0 6px 12px rgba(7, 72, 31, 0.22);
  flex: 0 0 auto;
}

.whatsapp-fab-icono {
  width: 1.36rem;
  height: 1.36rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.whatsapp-fab-icono svg {
  width: 100%;
  height: 100%;
  display: block;
}

.whatsapp-fab-copy {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.04;
}

.whatsapp-fab-texto {
  font-size: 0.94rem;
  font-weight: 900;
  letter-spacing: 0.015em;
  white-space: nowrap;
}

.whatsapp-fab-subtexto {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: rgba(242, 255, 247, 0.94);
  white-space: nowrap;
}

.whatsapp-fab-status {
  width: 0.58rem;
  height: 0.58rem;
  border-radius: 50%;
  background: #e8ffef;
  box-shadow: 0 0 0 0 rgba(232, 255, 239, 0.65);
  flex: 0 0 auto;
  animation: whatsapp-fab-status-pulse 1.9s ease-in-out infinite;
}

.whatsapp-fab--hidden {
  opacity: 0;
  pointer-events: none;
  animation: none !important;
  transform: translateY(14px) scale(0.94);
}

.whatsapp-fab::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.28);
  pointer-events: none;
}

:global(body.carrito-bloqueo-scroll .whatsapp-fab) {
  opacity: 0;
  pointer-events: none;
  animation: none !important;
  transform: translateY(12px);
}

@keyframes whatsapp-fab-float {
  0% {
    transform: translateY(0) rotate(-1deg);
  }
  50% {
    transform: translateY(-6px) rotate(1deg);
  }
  100% {
    transform: translateY(0) rotate(-1deg);
  }
}

@keyframes whatsapp-fab-glow {
  0% {
    box-shadow: 0 14px 24px rgba(12, 93, 42, 0.3);
  }
  50% {
    box-shadow: 0 22px 38px rgba(12, 93, 42, 0.44);
  }
  100% {
    box-shadow: 0 14px 24px rgba(12, 93, 42, 0.3);
  }
}

@keyframes whatsapp-fab-shine {
  0% {
    left: -52%;
    opacity: 0;
  }
  8% {
    opacity: 1;
  }
  28% {
    left: 118%;
    opacity: 0;
  }
  100% {
    left: 118%;
    opacity: 0;
  }
}

@keyframes whatsapp-fab-status-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(232, 255, 239, 0.6);
  }
  70% {
    box-shadow: 0 0 0 0.48rem rgba(232, 255, 239, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(232, 255, 239, 0);
  }
}

@media (max-width: 768px) {
  .whatsapp-fab {
    right: calc(1.02rem + env(safe-area-inset-right));
    bottom: calc(0.9rem + env(safe-area-inset-bottom));
    width: 3.8rem;
    height: 3.8rem;
    min-height: 3.8rem;
    padding: 0;
    justify-content: center;
    border-radius: 50%;
  }

  .whatsapp-fab-icono-wrap {
    width: 2.4rem;
    height: 2.4rem;
  }

  .whatsapp-fab-icono {
    width: 1.44rem;
    height: 1.44rem;
  }

  .whatsapp-fab-copy,
  .whatsapp-fab-status {
    display: none;
  }
}
</style>
