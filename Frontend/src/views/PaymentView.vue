<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { ROUTES } from '../config/routes'
import {
  CHECKOUT_CARD_SCHEMES,
  CHECKOUT_ENV,
  CHECKOUT_LOCALE,
  CHECKOUT_PERSONA_SDK_URL,
  CHECKOUT_POLLING_MS,
  CHECKOUT_WEB_COMPONENTS_URL,
} from '../config/checkout'
import { CONTACT_INFO } from '../config/constants'
import {
  extractPaymentErrorMessage,
  formatPaymentStatusLabel,
  isPaymentStatusFailed,
  isPaymentStatusSuccessful,
  isPaymentStatusTerminal,
  obtenerEstadoPagoPorToken,
  requiresPaymentKyc,
} from '../services/paymentsService'
import { construirEnlaceWhatsapp } from '../utils/whatsapp'
import { formatearErrorCheckout } from '../utils/checkoutPresentation'
import { loadExternalModule, preloadExternalModule } from '../utils/externalModuleLoader'
import { usePageMeta } from '../utils/usePageMeta'

const route = useRoute()
const checkoutContainerRef = ref(null)

const loading = ref(true)
const refreshing = ref(false)
const mountingCheckout = ref(false)
const openingKyc = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const payment = ref(null)

let pollTimer = null
let requestInFlight = false

const paymentToken = computed(() => String(route.params.paymentToken || '').trim())
const paymentStatus = computed(() => String(payment.value?.status || '').trim().toLowerCase())
const paymentStatusLabel = computed(() => formatPaymentStatusLabel(paymentStatus.value))
const isPaid = computed(() => isPaymentStatusSuccessful(paymentStatus.value))
const isFailed = computed(() => isPaymentStatusFailed(paymentStatus.value))
const isTerminal = computed(() => isPaymentStatusTerminal(paymentStatus.value))
const needsKyc = computed(() => requiresPaymentKyc(paymentStatus.value))

const orderSummary = computed(() => {
  const order = payment.value?.order || null
  if (!order) return null
  return {
    id: order.id,
    referencia: order.referencia,
    total: Number(order.total || 0),
    currency: String(order.currency || 'USD').trim().toUpperCase() || 'USD',
  }
})

const supportWhatsappNumber = computed(() => {
  const providerNumber = String(payment.value?.support?.whatsappNumber || '').trim()
  if (providerNumber) return providerNumber
  return CONTACT_INFO.whatsappDigits
})

const supportWhatsappLink = computed(() => {
  const summary = orderSummary.value
  const message = [
    'Hola, necesito soporte con mi compra en EventTix.',
    summary ? `Pedido: #${summary.id} / ${summary.referencia}` : '',
    `Estado: ${paymentStatusLabel.value}`,
  ]
    .filter(Boolean)
    .join('\n')

  return construirEnlaceWhatsapp(supportWhatsappNumber.value, message)
})

const checkoutAvailable = computed(() => {
  return Boolean(payment.value?.checkout?.publicKey && payment.value?.checkout?.session)
})

const showCheckout = computed(() => checkoutAvailable.value && !isTerminal.value && !needsKyc.value)

const accessCredentials = computed(() => {
  const creds = payment.value?.accessCredentials
  if (!creds?.email) return null
  return {
    email: creds.email,
    password: creds.password || null,
  }
})

usePageMeta({
  title: 'Pago seguro | EventTix',
  description: 'Finaliza y consulta el estado de tu pago con un flujo seguro y profesional en EventTix.',
  indexable: false,
})

function formatMoney(value) {
  return Number(value || 0).toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPollingIfNeeded() {
  if (pollTimer || isTerminal.value || !paymentToken.value) return
  pollTimer = setInterval(() => {
    void loadPayment({ silent: true })
  }, CHECKOUT_POLLING_MS)
}

async function mountCheckoutIfNeeded() {
  if (!showCheckout.value || !checkoutContainerRef.value || mountingCheckout.value) return

  const checkout = payment.value?.checkout
  if (!checkout?.publicKey || !checkout?.session) return

  mountingCheckout.value = true
  try {
    if (!CHECKOUT_WEB_COMPONENTS_URL) {
      throw new Error('Falta configurar VITE_CHECKOUT_WEB_COMPONENTS_URL')
    }

    await nextTick()

    const checkoutModule = await loadExternalModule(CHECKOUT_WEB_COMPONENTS_URL)
    const loadCheckoutWebComponents = checkoutModule?.loadCheckoutWebComponents

    if (typeof loadCheckoutWebComponents !== 'function') {
      throw new Error('No se pudo cargar el SDK de Checkout')
    }

    checkoutContainerRef.value.innerHTML = ''

    const widget = await loadCheckoutWebComponents({
      publicKey: checkout.publicKey,
      paymentSession: checkout.session,
      environment: CHECKOUT_ENV,
      locale: CHECKOUT_LOCALE,
      componentOptions: {
        flow: {
          expandFirstPaymentMethod: true,
          acceptedCardSchemes: CHECKOUT_CARD_SCHEMES,
        },
      },
      onPaymentCompleted: async () => {
        statusMessage.value = 'Pago enviado. Validando estado...'
        await loadPayment({ silent: true })
      },
      onError: async (_component, error) => {
        const details = formatearErrorCheckout(error)
        statusMessage.value = `Error de checkout: ${details.message}`
        await loadPayment({ silent: true })
      },
    })

    widget.create('flow').mount('#payment-checkout-container')
  } catch (error) {
    statusMessage.value = extractPaymentErrorMessage(error, 'No se pudo cargar la pasarela de pago.')
  } finally {
    mountingCheckout.value = false
  }
}

async function openKyc() {
  const kyc = payment.value?.kyc
  if (!kyc?.templateId || !kyc?.referenceId || !kyc?.environmentId || openingKyc.value) {
    return
  }

  openingKyc.value = true
  try {
    if (!CHECKOUT_PERSONA_SDK_URL) {
      throw new Error('Falta configurar VITE_PERSONA_SDK_URL')
    }

    const personaModule = await loadExternalModule(CHECKOUT_PERSONA_SDK_URL)
    const PersonaClient = personaModule?.Client

    if (typeof PersonaClient !== 'function') {
      throw new Error('No se pudo iniciar Persona KYC')
    }

    const client = new PersonaClient({
      templateId: kyc.templateId,
      referenceId: kyc.referenceId,
      environmentId: kyc.environmentId,
      onReady: () => client.open(),
      onComplete: async () => {
        statusMessage.value = 'KYC completado. Verificando pago...'
        await loadPayment({ silent: true })
      },
      onError: (error) => {
        statusMessage.value = `Error en KYC: ${String(error?.message || error || 'desconocido')}`
      },
    })
  } catch (error) {
    statusMessage.value = extractPaymentErrorMessage(error, 'No se pudo abrir el flujo KYC.')
  } finally {
    openingKyc.value = false
  }
}

async function loadPayment({ silent = false } = {}) {
  if (!paymentToken.value || requestInFlight) return

  requestInFlight = true
  if (!silent) {
    loading.value = true
    errorMessage.value = ''
  } else {
    refreshing.value = true
  }

  try {
    const response = await obtenerEstadoPagoPorToken({
      paymentToken: paymentToken.value,
      syncOrder: true,
    })

    payment.value = response
    errorMessage.value = ''

    if (isTerminal.value) {
      stopPolling()
    }

    await mountCheckoutIfNeeded()
    startPollingIfNeeded()
  } catch (error) {
    errorMessage.value = extractPaymentErrorMessage(error, 'No se pudo consultar el estado del pago.')
  } finally {
    loading.value = false
    refreshing.value = false
    requestInFlight = false
  }
}

watch(
  () => paymentToken.value,
  () => {
    stopPolling()
    payment.value = null
    statusMessage.value = ''
    void loadPayment()
  }
)

onMounted(() => {
  preloadExternalModule(CHECKOUT_WEB_COMPONENTS_URL)
  preloadExternalModule(CHECKOUT_PERSONA_SDK_URL)
  void loadPayment()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <section class="payment-page py-4 py-lg-5">
    <div class="container payment-container">
      <header class="payment-header mb-4">
        <h1 class="payment-title mb-1">Estado de pago</h1>
        <p class="payment-subtitle mb-0">Consulta y completa tu pago de forma segura.</p>
      </header>

      <p v-if="errorMessage" class="alert alert-danger mb-4">{{ errorMessage }}</p>

      <div v-if="loading" class="card border-0 shadow-sm p-4">
        <p class="mb-0">Cargando información del pago...</p>
      </div>

      <template v-else-if="payment">
        <div class="row g-4">
          <div class="col-12 col-lg-5">
            <article class="card border-0 shadow-sm h-100 payment-card">
              <div class="card-body">
                <h2 class="h6 text-uppercase text-muted mb-3">Resumen del pedido</h2>
                <p class="mb-1"><strong>Estado:</strong> {{ paymentStatusLabel }}</p>
                <p class="mb-1"><strong>Payment ID:</strong> {{ payment.paymentId || 'No disponible' }}</p>
                <p class="mb-1"><strong>Pedido:</strong> #{{ orderSummary?.id || 'N/D' }}</p>
                <p class="mb-1"><strong>Referencia:</strong> {{ orderSummary?.referencia || 'N/D' }}</p>
                <p class="mb-0">
                  <strong>Total:</strong>
                  {{ formatMoney(orderSummary?.total) }} {{ orderSummary?.currency || 'USD' }}
                </p>
              </div>
            </article>
          </div>

          <div class="col-12 col-lg-7">
            <article class="card border-0 shadow-sm payment-card">
              <div class="card-body">
                <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                  <h2 class="h6 text-uppercase text-muted mb-0">Método de pago</h2>
                  <button class="btn btn-outline-dark btn-sm" type="button" :disabled="refreshing" @click="loadPayment()">
                    {{ refreshing ? 'Actualizando...' : 'Actualizar estado' }}
                  </button>
                </div>

                <p class="mb-3">Proveedor: Crossmint / Checkout.com</p>

                <div v-if="isPaid" class="alert alert-success mb-3">
                  <strong>Pago confirmado.</strong>
                  <p class="mb-0 mt-1">Tu compra fue validada correctamente.</p>
                </div>

                <div v-if="isFailed" class="alert alert-danger mb-3">
                  <strong>Pago no completado.</strong>
                  <p class="mb-0 mt-1">Verifica el método de pago o contacta soporte.</p>
                </div>

                <div v-if="accessCredentials" class="alert alert-info mb-3">
                  <strong>Credenciales de acceso</strong>
                  <p class="mb-1 mt-1">Correo: {{ accessCredentials.email }}</p>
                  <p v-if="accessCredentials.password" class="mb-1">Contraseña temporal: {{ accessCredentials.password }}</p>
                  <p v-else class="mb-1">Usa la contraseña que ya tienes registrada.</p>
                  <RouterLink class="btn btn-sm btn-dark mt-2" :to="ROUTES.login">Ir a iniciar sesión</RouterLink>
                </div>

                <section v-if="showCheckout" class="payment-checkout-wrap">
                  <h3 class="h6 mb-2">Completa tu pago</h3>
                  <div id="payment-checkout-container" ref="checkoutContainerRef" class="payment-checkout-container" />
                </section>

                <section v-if="needsKyc" class="payment-kyc-wrap">
                  <h3 class="h6 mb-2">Verificación KYC requerida</h3>
                  <button class="btn btn-dark btn-sm" type="button" :disabled="openingKyc" @click="openKyc">
                    {{ openingKyc ? 'Abriendo KYC...' : 'Abrir KYC' }}
                  </button>
                </section>

                <p v-if="statusMessage" class="text-muted mt-3 mb-0">{{ statusMessage }}</p>

                <div class="d-flex flex-wrap gap-2 mt-3">
                  <a
                    v-if="supportWhatsappLink"
                    class="btn btn-outline-dark btn-sm"
                    :href="supportWhatsappLink"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Contactar soporte por WhatsApp
                  </a>
                </div>
              </div>
            </article>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.payment-page {
  background: #f6f8fb;
  min-height: 70vh;
}

.payment-container {
  max-width: 1120px;
}

.payment-title {
  font-size: 1.85rem;
  font-weight: 700;
  color: #152034;
}

.payment-subtitle {
  color: #4d5b75;
}

.payment-card {
  border-radius: 14px;
}

.payment-checkout-wrap,
.payment-kyc-wrap {
  padding: 0.85rem;
  border: 1px solid #d9e0ea;
  border-radius: 12px;
  background: #ffffff;
}

.payment-checkout-container {
  min-height: 260px;
}
</style>
