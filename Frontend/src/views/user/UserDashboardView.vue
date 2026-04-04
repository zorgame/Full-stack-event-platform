<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import InternalPanelLayout from '../../components/layout/InternalPanelLayout.vue'
import { BRANDING, UI_TEXTS } from '../../config/constants'
import { ROUTES } from '../../config/routes'
import { persistUser } from '../../services/authService'
import { getSdkClient } from '../../services/sdkClient'
import { useAuthStore } from '../../stores/auth'

const SETTINGS_STORAGE_KEY = 'tickets_user_preferences_v1'
const AUTO_REFRESH_MIN_INTERVAL_MS = 75_000

const SECTION_OPTIONS = [
  { id: 'perfil', label: 'Perfil' },
  { id: 'tickets', label: 'Tickets' },
  { id: 'settings', label: 'Settings' },
  { id: 'facturacion', label: 'Facturacion' },
]

const languageOptions = [
  { value: 'es', label: 'Espanol' },
  { value: 'en', label: 'English' },
]

const timezoneOptions = [
  { value: 'America/Santo_Domingo', label: 'America/Santo Domingo (GMT-4)' },
  { value: 'America/Bogota', label: 'America/Bogota (GMT-5)' },
  { value: 'America/Mexico_City', label: 'America/Mexico City (GMT-6)' },
  { value: 'Europe/Madrid', label: 'Europe/Madrid (GMT+1)' },
]

const ticketViewOptions = [
  { value: 'compacta', label: 'Vista compacta' },
  { value: 'detallada', label: 'Vista detallada' },
]

const defaultSettings = {
  receivePurchaseEmails: true,
  receiveTransferAlerts: true,
  receiveLoginAlerts: true,
  preferredLanguage: 'es',
  timezone: 'America/Santo_Domingo',
  ticketView: 'detallada',
}

const DATE_FORMATTER = new Intl.DateTimeFormat('es-DO', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const moneyFormatterCache = new Map()
let userDocumentsModulePromise = null

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const activeSection = ref('perfil')
const panelLoading = ref(false)
const panelError = ref('')
const pedidos = ref([])
const productos = ref([])

const ticketPdfLoadingKey = ref('')
const ticketActionMessage = reactive({
  type: '',
  text: '',
})

const billingPdfLoading = ref(false)
const billingMessage = reactive({
  type: '',
  text: '',
})

const showFifaNotice = ref(false)
const fifaTicket = ref(null)
const showTransferModal = ref(false)
const transferTicket = ref(null)
const lastPanelSyncAt = ref(0)

const transferDraft = reactive({
  ticketKey: '',
  recipientName: '',
  recipientEmail: '',
  quantity: 1,
  password: '',
  notes: '',
  confirmation: false,
})

const transferSubmitting = ref(false)
const transferMessage = reactive({
  type: '',
  text: '',
})
const transferHistory = ref([])

const settings = reactive({ ...defaultSettings })
const settingsMessage = reactive({
  type: '',
  text: '',
})

function normalizeSection(value) {
  const normalized = String(value || '').trim().toLowerCase()
  return SECTION_OPTIONS.some((item) => item.id === normalized) ? normalized : 'perfil'
}

function asNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function formatDate(value) {
  if (!value) return 'No disponible'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No disponible'
  return DATE_FORMATTER.format(date)
}

function getCurrencyFormatter(currency = 'USD') {
  const key = String(currency || 'USD').toUpperCase() || 'USD'
  if (!moneyFormatterCache.has(key)) {
    moneyFormatterCache.set(
      key,
      new Intl.NumberFormat('es-DO', {
        style: 'currency',
        currency: key,
        maximumFractionDigits: 2,
      }),
    )
  }
  return moneyFormatterCache.get(key)
}

function formatCurrency(value, currency = 'USD') {
  return getCurrencyFormatter(currency).format(asNumber(value))
}

function normalizeOrderStatus(status) {
  return String(status || '').trim().toLowerCase()
}

function orderStatusLabel(status) {
  const normalized = normalizeOrderStatus(status)
  if (normalized === 'pagado') return 'Pagado'
  if (normalized === 'pendiente') return 'Pendiente'
  if (normalized === 'cancelado') return 'Cancelado'
  if (normalized === 'fallido') return 'Rechazado'
  return 'En revision'
}

function orderStatusClass(status) {
  const normalized = normalizeOrderStatus(status)
  if (normalized === 'pagado') return 'status-success'
  if (normalized === 'pendiente') return 'status-warning'
  if (normalized === 'cancelado' || normalized === 'fallido') return 'status-danger'
  return 'status-neutral'
}

function parseSettings(raw) {
  return {
    receivePurchaseEmails: Boolean(raw?.receivePurchaseEmails ?? defaultSettings.receivePurchaseEmails),
    receiveTransferAlerts: Boolean(raw?.receiveTransferAlerts ?? defaultSettings.receiveTransferAlerts),
    receiveLoginAlerts: Boolean(raw?.receiveLoginAlerts ?? defaultSettings.receiveLoginAlerts),
    preferredLanguage:
      raw?.preferredLanguage === 'en' || raw?.preferredLanguage === 'es'
        ? raw.preferredLanguage
        : defaultSettings.preferredLanguage,
    timezone: timezoneOptions.some((option) => option.value === raw?.timezone)
      ? raw.timezone
      : defaultSettings.timezone,
    ticketView: ticketViewOptions.some((option) => option.value === raw?.ticketView)
      ? raw.ticketView
      : defaultSettings.ticketView,
  }
}

function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (!raw) {
      Object.assign(settings, defaultSettings)
      return
    }
    const parsed = JSON.parse(raw)
    Object.assign(settings, parseSettings(parsed))
  } catch {
    Object.assign(settings, defaultSettings)
  }
}

function saveSettings() {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
    settingsMessage.type = 'success'
    settingsMessage.text = 'Preferencias guardadas correctamente.'
  } catch {
    settingsMessage.type = 'danger'
    settingsMessage.text = 'No fue posible guardar tus preferencias en este navegador.'
  }
}

function resetSettings() {
  Object.assign(settings, defaultSettings)
  saveSettings()
}

async function getUserDocumentsModule() {
  if (!userDocumentsModulePromise) {
    userDocumentsModulePromise = import('../../utils/userDocuments')
  }
  return userDocumentsModulePromise
}

const currentUser = computed(() => authStore.user || null)

const userFullName = computed(() => {
  const full = `${currentUser.value?.nombre || ''} ${currentUser.value?.apellido || ''}`.trim()
  return full || currentUser.value?.email || 'Cliente Tickets Nova'
})

const userInitials = computed(() => {
  const words = userFullName.value.split(/\s+/).filter(Boolean)
  if (!words.length) return 'TN'
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join('')
})

const productByCategoryId = computed(() => {
  const map = new Map()
  for (const product of productos.value) {
    const productId = asNumber(product?.id)
    const eventName = String(product?.nombre || `Evento ${productId || ''}`).trim() || 'Evento'

    for (const category of product?.categorias || []) {
      const categoryId = asNumber(category?.id)
      if (!categoryId) continue
      map.set(categoryId, {
        eventName,
        categoryName: String(category?.nombre || `Categoria ${categoryId}`).trim(),
        price: asNumber(category?.precio),
        currency: String(category?.moneda || 'USD').trim().toUpperCase() || 'USD',
      })
    }
  }
  return map
})

const pedidosOrdenados = computed(() => {
  return [...pedidos.value].sort((a, b) => {
    const dateA = new Date(a?.fecha_creacion || 0).getTime()
    const dateB = new Date(b?.fecha_creacion || 0).getTime()
    return dateB - dateA
  })
})

const pedidosPagados = computed(() => {
  return pedidosOrdenados.value.filter((pedido) => normalizeOrderStatus(pedido?.estado) === 'pagado')
})

const ticketsFromAccount = computed(() => {
  const source = Array.isArray(currentUser.value?.tickets) ? currentUser.value.tickets : []

  return source
    .map((item, index) => {
      const categoryId = asNumber(item?.categoria_id ?? item?.categoria?.id)
      const fallbackCategory = productByCategoryId.value.get(categoryId)
      const categoryName =
        String(item?.categoria?.nombre || fallbackCategory?.categoryName || '').trim() || 'Categoria'
      const eventName =
        String(fallbackCategory?.eventName || `Evento #${item?.categoria?.producto_id || categoryId || index + 1}`)
          .trim()
      const currency =
        String(item?.categoria?.moneda || fallbackCategory?.currency || 'USD').trim().toUpperCase() || 'USD'

      return {
        key: `usr-${item?.id || `${categoryId}-${index}`}`,
        id: asNumber(item?.id),
        usuarioTicketId: asNumber(item?.id),
        sourceType: 'asignado',
        categoriaId: categoryId,
        categoriaNombre: categoryName,
        eventoNombre: eventName,
        cantidad: asNumber(item?.cantidad),
        precio: asNumber(item?.categoria?.precio ?? fallbackCategory?.price),
        moneda: currency,
        nota: String(item?.nota || '').trim(),
        codigo: `TN-${asNumber(currentUser.value?.id) || 'U'}-${asNumber(item?.id) || categoryId || index + 1}`,
        createdAt: item?.created_at || item?.updated_at || null,
      }
    })
    .filter((row) => row.cantidad > 0)
})

const ticketsFromPaidOrders = computed(() => {
  const grouped = new Map()

  for (const order of pedidosPagados.value) {
    for (const detail of order?.detalles || []) {
      const categoryId = asNumber(detail?.categoria_id)
      if (!categoryId) continue

      const fallbackCategory = productByCategoryId.value.get(categoryId)
      const categoryName =
        String(detail?.categoria?.nombre || fallbackCategory?.categoryName || '').trim() || 'Categoria'
      const eventName =
        String(fallbackCategory?.eventName || `Evento #${detail?.categoria?.producto_id || categoryId}`).trim()
      const currency =
        String(detail?.categoria?.moneda || fallbackCategory?.currency || 'USD').trim().toUpperCase() || 'USD'

      if (!grouped.has(categoryId)) {
        grouped.set(categoryId, {
          key: `ord-${categoryId}`,
          id: categoryId,
          usuarioTicketId: null,
          sourceType: 'pedido',
          categoriaId: categoryId,
          categoriaNombre: categoryName,
          eventoNombre: eventName,
          cantidad: 0,
          precio: asNumber(detail?.precio_unitario ?? fallbackCategory?.price),
          moneda: currency,
          nota: 'Consolidado desde pedidos pagados',
          codigo: `PD-${categoryId}`,
          createdAt: order?.fecha_creacion || null,
        })
      }

      const existing = grouped.get(categoryId)
      existing.cantidad += asNumber(detail?.cantidad)
    }
  }

  return Array.from(grouped.values())
})

const ticketsUsuario = computed(() => {
  if (ticketsFromAccount.value.length) return ticketsFromAccount.value
  return ticketsFromPaidOrders.value
})

const totalTickets = computed(() => {
  return ticketsUsuario.value.reduce((acc, ticket) => acc + asNumber(ticket.cantidad), 0)
})

const totalFacturado = computed(() => {
  return pedidosPagados.value.reduce((acc, pedido) => acc + asNumber(pedido.total), 0)
})

const totalPendiente = computed(() => {
  return pedidosOrdenados.value
    .filter((pedido) => normalizeOrderStatus(pedido?.estado) === 'pendiente')
    .reduce((acc, pedido) => acc + asNumber(pedido.total), 0)
})

const profileRows = computed(() => {
  const user = currentUser.value
  return [
    { label: 'Nombre completo', value: userFullName.value },
    { label: 'Email', value: user?.email || 'No disponible' },
    { label: 'Telefono', value: user?.telefono || 'No registrado' },
    { label: 'Pais', value: user?.pais || 'No registrado' },
    { label: 'Miembro desde', value: formatDate(user?.created_at) },
    {
      label: 'Ultima actualizacion',
      value: formatDate(user?.updated_at),
    },
  ]
})

const billingProfile = computed(() => {
  const latestOrder = pedidosOrdenados.value[0]
  return {
    nombre: latestOrder?.nombre_completo || userFullName.value,
    correo: latestOrder?.correo_electronico || currentUser.value?.email || 'No disponible',
    telefono: latestOrder?.telefono || currentUser.value?.telefono || 'No disponible',
    pais: latestOrder?.pais || currentUser.value?.pais || 'No disponible',
    documento: latestOrder?.documento || 'No disponible',
  }
})

const transferButtonLabel = computed(() => {
  const target = transferDraft.recipientName.trim() || transferDraft.recipientEmail.trim() || 'el destinatario indicado'
  return `Estas seguro que quieres transferir estos tickets a ${target}?`
})

function clearTicketActionMessage() {
  ticketActionMessage.type = ''
  ticketActionMessage.text = ''
}

function clearTransferMessage() {
  transferMessage.type = ''
  transferMessage.text = ''
}

function resetTransferDraft() {
  transferDraft.ticketKey = ''
  transferDraft.recipientName = ''
  transferDraft.recipientEmail = ''
  transferDraft.quantity = 1
  transferDraft.password = ''
  transferDraft.notes = ''
  transferDraft.confirmation = false
}

function selectSection(sectionId) {
  const normalized = normalizeSection(sectionId)
  activeSection.value = normalized
  router.replace({
    path: ROUTES.user,
    query: {
      ...route.query,
      section: normalized,
    },
  })
}

async function loadUserPanel() {
  if (panelLoading.value) return

  panelLoading.value = true
  panelError.value = ''

  try {
    const sdk = getSdkClient()
    const [me, myOrders, products] = await Promise.all([
      sdk.auth.me(),
      sdk.pedidos.mine(),
      sdk.productos.list({ skip: 0, limit: 500, only_active: false }),
    ])

    authStore.user = me
    persistUser(me)
    pedidos.value = Array.isArray(myOrders) ? myOrders : []
    productos.value = Array.isArray(products) ? products : []
    lastPanelSyncAt.value = Date.now()
  } catch (error) {
    panelError.value = error?.message || 'No fue posible cargar tu panel de cuenta.'
  } finally {
    panelLoading.value = false
  }
}

function shouldAutoRefresh() {
  const elapsed = Date.now() - Number(lastPanelSyncAt.value || 0)
  return elapsed >= AUTO_REFRESH_MIN_INTERVAL_MS
}

function refreshPanelIfNeeded() {
  if (!shouldAutoRefresh()) return
  loadUserPanel()
}

function onVisibilityChange() {
  if (document.visibilityState !== 'visible') return
  refreshPanelIfNeeded()
}

function openFifaNotice(ticket) {
  fifaTicket.value = ticket
  showFifaNotice.value = true
}

function closeFifaNotice() {
  fifaTicket.value = null
  showFifaNotice.value = false
}

async function downloadTicketPdf(ticket) {
  clearTicketActionMessage()
  ticketPdfLoadingKey.value = ticket.key

  try {
    const { downloadTicketReportPdf } = await getUserDocumentsModule()
    await downloadTicketReportPdf({
      brandName: UI_TEXTS.appName,
      brandLogoPath: BRANDING.logoPath,
      eventLogoPath: '/assets/fifa-logo.png',
      user: currentUser.value,
      ticket,
      tickets: ticketsUsuario.value,
      pedidos: pedidosPagados.value,
    })
    ticketActionMessage.type = 'success'
    ticketActionMessage.text = 'PDF del ticket generado correctamente.'
  } catch (error) {
    ticketActionMessage.type = 'danger'
    ticketActionMessage.text = error?.message || 'No se pudo generar el PDF del ticket.'
  } finally {
    ticketPdfLoadingKey.value = ''
  }
}

function openTransferPanel(ticket) {
  clearTransferMessage()
  transferTicket.value = ticket
  showTransferModal.value = true
  transferDraft.ticketKey = ticket.key
  transferDraft.recipientName = ''
  transferDraft.recipientEmail = ''
  transferDraft.quantity = 1
  transferDraft.password = ''
  transferDraft.notes = ''
  transferDraft.confirmation = false
}

function closeTransferPanel() {
  clearTransferMessage()
  showTransferModal.value = false
  transferTicket.value = null
  resetTransferDraft()
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim())
}

async function submitTransferRequest() {
  clearTransferMessage()
  const ticket = transferTicket.value

  if (!ticket) {
    transferMessage.type = 'danger'
    transferMessage.text = 'No se encontro el ticket para la transferencia.'
    return
  }

  const recipientName = transferDraft.recipientName.trim()
  const recipientEmail = transferDraft.recipientEmail.trim().toLowerCase()
  const quantity = asNumber(transferDraft.quantity)
  const password = String(transferDraft.password || '')

  if (!Number.isInteger(asNumber(ticket?.usuarioTicketId)) || asNumber(ticket?.usuarioTicketId) <= 0) {
    transferMessage.type = 'danger'
    transferMessage.text = 'Este ticket no esta habilitado para transferencia directa desde tu cuenta.'
    return
  }

  if (!recipientName) {
    transferMessage.type = 'danger'
    transferMessage.text = 'Debes indicar el nombre del destinatario.'
    return
  }

  if (!isValidEmail(recipientEmail)) {
    transferMessage.type = 'danger'
    transferMessage.text = 'Ingresa un correo valido del destinatario.'
    return
  }

  if (!Number.isInteger(quantity) || quantity < 1 || quantity > asNumber(ticket.cantidad)) {
    transferMessage.type = 'danger'
    transferMessage.text = 'La cantidad a transferir no es valida para este ticket.'
    return
  }

  if (!transferDraft.confirmation) {
    transferMessage.type = 'danger'
    transferMessage.text = 'Debes confirmar explicitamente la transferencia antes de continuar.'
    return
  }

  if (!password) {
    transferMessage.type = 'danger'
    transferMessage.text = 'Es obligatorio validar tu contrasena para autorizar la transferencia.'
    return
  }

  transferSubmitting.value = true

  try {
    const sdk = getSdkClient()
    const transferResult = await sdk.usuarios.transferMyTicket({
      usuario_ticket_id: asNumber(ticket.usuarioTicketId),
      destinatario_email: recipientEmail,
      cantidad: quantity,
      password,
      confirmacion_expresa: transferDraft.confirmation,
      nota: transferDraft.notes || null,
    })

    transferHistory.value.unshift({
      id: transferResult?.transferencia_id || `TR-${Date.now()}`,
      ticket: ticket.categoriaNombre,
      evento: ticket.eventoNombre,
      destinatario: recipientName,
      correo: recipientEmail,
      cantidad: quantity,
      estado: transferResult?.estado === 'procesada' ? 'Procesada' : 'Pendiente de validacion interna',
      fecha: transferResult?.fecha || new Date().toISOString(),
    })

    await loadUserPanel()

    ticketActionMessage.type = 'success'
    ticketActionMessage.text = 'Transferencia aplicada y notificada por correo.'
    closeTransferPanel()
  } catch (error) {
    transferMessage.type = 'danger'
    transferMessage.text = error?.message || 'No pudimos validar tu contrasena. Verifica los datos e intenta nuevamente.'
  } finally {
    transferSubmitting.value = false
  }
}

async function downloadBillingPdf() {
  billingMessage.type = ''
  billingMessage.text = ''
  billingPdfLoading.value = true

  try {
    const { downloadBillingReportPdf } = await getUserDocumentsModule()
    await downloadBillingReportPdf({
      brandName: UI_TEXTS.appName,
      brandLogoPath: BRANDING.logoPath,
      eventLogoPath: '/assets/fifa-logo.png',
      user: currentUser.value,
      pedidos: pedidosOrdenados.value,
    })
    billingMessage.type = 'success'
    billingMessage.text = 'PDF de facturacion generado correctamente.'
  } catch (error) {
    billingMessage.type = 'danger'
    billingMessage.text = error?.message || 'No fue posible generar el PDF de facturacion.'
  } finally {
    billingPdfLoading.value = false
  }
}

watch(
  () => route.query.section,
  (value) => {
    activeSection.value = normalizeSection(value)
  },
  { immediate: true },
)

onMounted(() => {
  loadSettings()
  loadUserPanel()
  window.addEventListener('focus', refreshPanelIfNeeded)
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  window.removeEventListener('focus', refreshPanelIfNeeded)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <div class="user-dashboard-page-root">
    <InternalPanelLayout :title="UI_TEXTS.userPanel.title" :subtitle="UI_TEXTS.userPanel.subtitle">
      <div class="col-12">
        <section class="user-dashboard-shell">
        <header class="dashboard-hero">
          <div class="dashboard-identity">
            <span class="identity-badge">{{ userInitials }}</span>
            <div>
              <p class="dashboard-kicker mb-1">Centro de cuenta</p>
              <h2 class="h4 fw-bold mb-1">{{ userFullName }}</h2>
              <p class="text-muted mb-0">
                Gestiona tu perfil, tus tickets, configuraciones seguras y documentos de facturacion.
              </p>
            </div>
          </div>
        </header>

        <div class="kpi-grid">
          <article class="kpi-card">
            <p class="kpi-label">Tickets activos</p>
            <p class="kpi-value">{{ totalTickets }}</p>
            <p class="kpi-caption">Inventario asociado a tu cuenta.</p>
          </article>
          <article class="kpi-card">
            <p class="kpi-label">Facturado pagado</p>
            <p class="kpi-value">{{ formatCurrency(totalFacturado, 'USD') }}</p>
            <p class="kpi-caption">Total consolidado de pedidos pagados.</p>
          </article>
          <article class="kpi-card">
            <p class="kpi-label">Monto pendiente</p>
            <p class="kpi-value">{{ formatCurrency(totalPendiente, 'USD') }}</p>
            <p class="kpi-caption">Pedidos en estado pendiente de validacion.</p>
          </article>
        </div>

        <nav class="account-tabs" aria-label="Secciones del panel de usuario">
          <button
            v-for="section in SECTION_OPTIONS"
            :key="section.id"
            type="button"
            class="account-tab"
            :class="activeSection === section.id ? 'account-tab-active' : ''"
            @click="selectSection(section.id)"
          >
            {{ section.label }}
          </button>
        </nav>

        <div v-if="panelError" class="alert alert-danger mt-3 mb-0" role="alert">
          {{ panelError }}
        </div>

        <div v-if="panelLoading" class="panel-loading mt-3">
          <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
          <span>Cargando recursos del panel...</span>
        </div>

        <section v-if="activeSection === 'perfil'" class="section-block">
          <article class="section-card">
            <h3 class="h5 fw-bold mb-3">Informacion de perfil</h3>
            <div class="profile-grid">
              <div v-for="row in profileRows" :key="row.label" class="profile-row">
                <p class="profile-label mb-1">{{ row.label }}</p>
                <p class="profile-value mb-0">{{ row.value }}</p>
              </div>
            </div>
          </article>

          <article class="section-card">
            <h3 class="h5 fw-bold mb-3">Recomendaciones de seguridad</h3>
            <ul class="security-list mb-0">
              <li>Activa alertas de inicio de sesion para identificar accesos nuevos.</li>
              <li>No compartas enlaces de acceso ni capturas completas de tus tickets.</li>
              <li>Descarga tus reportes PDF solo desde dispositivos confiables.</li>
            </ul>
          </article>
        </section>

        <section v-if="activeSection === 'tickets'" class="section-block">
          <article class="section-card">
            <div class="section-heading">
              <div>
                <h3 class="h5 fw-bold mb-1">Mis tickets</h3>
                <p class="text-muted mb-0">
                  Aqui puedes ver tus tickets por categoria y ejecutar acciones seguras por cada boleto.
                </p>
              </div>
              <button class="btn btn-outline-secondary btn-sm fw-semibold" type="button" @click="selectSection('facturacion')">
                Ir a facturacion
              </button>
            </div>

            <div v-if="ticketActionMessage.text" class="alert mt-3 mb-0" :class="`alert-${ticketActionMessage.type}`" role="alert">
              {{ ticketActionMessage.text }}
            </div>

            <div v-if="!ticketsUsuario.length" class="empty-state mt-3">
              Aun no tienes tickets asignados. Cuando se confirme un pedido pagado, apareceran aqui.
            </div>

            <div v-else class="ticket-grid mt-3">
              <article v-for="ticket in ticketsUsuario" :key="ticket.key" class="ticket-card">
                <div class="ticket-card-header">
                  <div>
                    <p class="ticket-kicker mb-1">{{ ticket.eventoNombre }}</p>
                    <h4 class="h6 fw-bold mb-0">{{ ticket.categoriaNombre }}</h4>
                  </div>
                  <span class="ticket-qty">x{{ ticket.cantidad }}</span>
                </div>

                <div class="ticket-meta-grid" :class="settings.ticketView === 'compacta' ? 'ticket-meta-grid-compact' : ''">
                  <div>
                    <p class="meta-label">Codigo</p>
                    <p class="meta-value">{{ ticket.codigo }}</p>
                  </div>
                  <div>
                    <p class="meta-label">Precio unitario</p>
                    <p class="meta-value">{{ formatCurrency(ticket.precio, ticket.moneda) }}</p>
                  </div>
                  <div>
                    <p class="meta-label">Moneda</p>
                    <p class="meta-value">{{ ticket.moneda }}</p>
                  </div>
                  <div>
                    <p class="meta-label">Ultimo movimiento</p>
                    <p class="meta-value">{{ formatDate(ticket.createdAt) }}</p>
                  </div>
                </div>

                <p v-if="ticket.nota" class="ticket-note mb-0">
                  {{ ticket.nota }}
                </p>

                <div class="ticket-actions">
                  <button class="btn btn-outline-danger btn-sm fw-semibold" type="button" @click="openFifaNotice(ticket)">
                    Transferir a FIFA
                  </button>
                  <button
                    class="btn btn-primary btn-sm fw-semibold"
                    type="button"
                    :disabled="ticketPdfLoadingKey === ticket.key"
                    @click="downloadTicketPdf(ticket)"
                  >
                    {{ ticketPdfLoadingKey === ticket.key ? 'Generando PDF...' : 'Imprimir' }}
                  </button>
                  <button
                    class="btn btn-outline-dark btn-sm fw-semibold"
                    type="button"
                    :disabled="!ticket.usuarioTicketId"
                    @click="openTransferPanel(ticket)"
                  >
                    Transferir a otra cuenta Ticket Nova
                  </button>
                </div>

                <p v-if="!ticket.usuarioTicketId" class="transfer-hint mb-0">
                  Este ticket proviene de consolidado de pedidos. Para transferirlo, primero debe estar asignado en tu cuenta.
                </p>
              </article>
            </div>
          </article>

          <article v-if="transferHistory.length" class="section-card">
            <h3 class="h5 fw-bold mb-3">Solicitudes recientes de transferencia</h3>
            <div class="table-responsive">
              <table class="table align-middle mb-0">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Ticket</th>
                    <th>Destinatario</th>
                    <th>Cantidad</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in transferHistory" :key="item.id">
                    <td>{{ formatDate(item.fecha) }}</td>
                    <td>
                      <p class="mb-0 fw-semibold">{{ item.ticket }}</p>
                      <small class="text-muted">{{ item.evento }}</small>
                    </td>
                    <td>
                      <p class="mb-0 fw-semibold">{{ item.destinatario }}</p>
                      <small class="text-muted">{{ item.correo }}</small>
                    </td>
                    <td>{{ item.cantidad }}</td>
                    <td>
                      <span class="badge rounded-pill text-bg-warning">{{ item.estado }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>

        <section v-if="activeSection === 'facturacion'" class="section-block">
          <article class="section-card">
            <div class="section-heading">
              <div>
                <h3 class="h5 fw-bold mb-1">Facturacion</h3>
                <p class="text-muted mb-0">
                  Resumen de identidad fiscal y trazabilidad completa de pedidos y cargos.
                </p>
              </div>
              <button class="btn btn-primary btn-sm fw-semibold" type="button" :disabled="billingPdfLoading" @click="downloadBillingPdf">
                {{ billingPdfLoading ? 'Generando PDF...' : 'Descargar PDF de facturacion' }}
              </button>
            </div>

            <div v-if="billingMessage.text" class="alert mt-3 mb-0" :class="`alert-${billingMessage.type}`" role="alert">
              {{ billingMessage.text }}
            </div>

            <div class="billing-grid mt-3">
              <div class="billing-card">
                <p class="billing-label">Titular</p>
                <p class="billing-value">{{ billingProfile.nombre }}</p>
              </div>
              <div class="billing-card">
                <p class="billing-label">Correo</p>
                <p class="billing-value">{{ billingProfile.correo }}</p>
              </div>
              <div class="billing-card">
                <p class="billing-label">Telefono</p>
                <p class="billing-value">{{ billingProfile.telefono }}</p>
              </div>
              <div class="billing-card">
                <p class="billing-label">Pais</p>
                <p class="billing-value">{{ billingProfile.pais }}</p>
              </div>
              <div class="billing-card">
                <p class="billing-label">Documento</p>
                <p class="billing-value">{{ billingProfile.documento }}</p>
              </div>
              <div class="billing-card billing-card-highlight">
                <p class="billing-label">Total pagado</p>
                <p class="billing-value">{{ formatCurrency(totalFacturado, 'USD') }}</p>
              </div>
            </div>
          </article>

          <article class="section-card">
            <h3 class="h5 fw-bold mb-3">Historial de pedidos para facturacion</h3>
            <div class="table-responsive">
              <table class="table align-middle mb-0">
                <thead>
                  <tr>
                    <th>Pedido</th>
                    <th>Referencia</th>
                    <th>Fecha</th>
                    <th>Estado</th>
                    <th>Conceptos</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!pedidosOrdenados.length">
                    <td colspan="6" class="text-center text-muted py-4">No hay pedidos para mostrar.</td>
                  </tr>
                  <tr v-for="pedido in pedidosOrdenados" :key="pedido.id">
                    <td>#{{ pedido.id }}</td>
                    <td>{{ pedido.referencia }}</td>
                    <td>{{ formatDate(pedido.fecha_creacion) }}</td>
                    <td>
                      <span class="status-badge" :class="orderStatusClass(pedido.estado)">
                        {{ orderStatusLabel(pedido.estado) }}
                      </span>
                    </td>
                    <td>{{ (pedido.detalles || []).length }}</td>
                    <td>{{ formatCurrency(pedido.total, 'USD') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>

        <section v-if="activeSection === 'settings'" class="section-block">
          <article class="section-card">
            <h3 class="h5 fw-bold mb-2">Settings seguros</h3>
            <p class="text-muted mb-4">
              Este bloque permite cambios que no afectan tus credenciales criticas ni la integridad de acceso a tu cuenta.
            </p>

            <div class="row g-3">
              <div class="col-12 col-md-6">
                <label class="form-label">Idioma preferido</label>
                <select v-model="settings.preferredLanguage" class="form-select">
                  <option v-for="option in languageOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <div class="col-12 col-md-6">
                <label class="form-label">Zona horaria</label>
                <select v-model="settings.timezone" class="form-select">
                  <option v-for="option in timezoneOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <div class="col-12 col-md-6">
                <label class="form-label">Preferencia de vista de tickets</label>
                <select v-model="settings.ticketView" class="form-select">
                  <option v-for="option in ticketViewOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <div class="col-12 col-md-6 d-flex flex-column justify-content-end">
                <div class="form-check mb-2">
                  <input id="settingPurchaseEmails" v-model="settings.receivePurchaseEmails" class="form-check-input" type="checkbox" />
                  <label class="form-check-label" for="settingPurchaseEmails">Recibir emails de compras y comprobantes</label>
                </div>
                <div class="form-check mb-2">
                  <input id="settingTransferAlerts" v-model="settings.receiveTransferAlerts" class="form-check-input" type="checkbox" />
                  <label class="form-check-label" for="settingTransferAlerts">Recibir alertas de transferencias de tickets</label>
                </div>
                <div class="form-check">
                  <input id="settingLoginAlerts" v-model="settings.receiveLoginAlerts" class="form-check-input" type="checkbox" />
                  <label class="form-check-label" for="settingLoginAlerts">Recibir alertas de inicios de sesion</label>
                </div>
              </div>
            </div>

            <div class="d-flex flex-wrap gap-2 mt-4">
              <button class="btn btn-primary fw-semibold" type="button" @click="saveSettings">
                Guardar settings
              </button>
              <button class="btn btn-outline-secondary fw-semibold" type="button" @click="resetSettings">
                Restaurar valores recomendados
              </button>
            </div>

            <div v-if="settingsMessage.text" class="alert mt-3 mb-0" :class="`alert-${settingsMessage.type}`" role="alert">
              {{ settingsMessage.text }}
            </div>
          </article>
        </section>
        </section>
      </div>
    </InternalPanelLayout>

    <div v-if="showFifaNotice" class="secure-modal-backdrop" @click.self="closeFifaNotice">
      <article class="secure-modal card border-0 shadow-lg">
        <div class="card-body p-4">
          <p class="secure-modal-kicker mb-2">Transferencia oficial a FIFA</p>
          <h3 class="h5 fw-bold mb-2">
            Politica de seguridad activa para {{ fifaTicket?.categoriaNombre || 'este ticket' }}
          </h3>
          <p class="text-muted mb-2">
            Esta opcion se habilita unicamente 15 dias antes del evento para proteger a nuestros clientes frente a fraude,
            suplantacion de identidad y movimientos no autorizados.
          </p>
          <p class="text-muted mb-4">
            La ventana de tiempo controlada nos permite validar titularidad, trazabilidad y cumplimiento antes de cualquier
            transferencia externa.
          </p>

          <div class="d-flex flex-wrap gap-2">
            <RouterLink class="btn btn-outline-secondary fw-semibold" :to="ROUTES.terminos" @click="closeFifaNotice">
              Ver politicas y condiciones
            </RouterLink>
            <button class="btn btn-primary fw-semibold" type="button" @click="closeFifaNotice">
              Entendido
            </button>
          </div>
        </div>
      </article>
    </div>

    <div v-if="showTransferModal" class="transfer-modal-backdrop" @click.self="closeTransferPanel">
      <article class="transfer-modal card border-0 shadow-lg">
        <div class="card-body p-4 p-lg-5">
          <div class="transfer-modal-head">
            <div>
              <p class="transfer-modal-kicker mb-1">Transferencia interna</p>
              <h3 class="h5 fw-bold mb-1">Enviar tickets a otra cuenta Ticket Nova</h3>
              <p class="text-muted mb-0">
                Confirma la operacion con doble seguridad y valida la titularidad antes de enviar.
              </p>
            </div>
            <button class="btn btn-sm btn-outline-secondary" type="button" @click="closeTransferPanel">Cerrar</button>
          </div>

          <div class="transfer-ticket-summary mt-3">
            <p class="mb-1 fw-semibold">{{ transferTicket?.categoriaNombre || 'Ticket seleccionado' }}</p>
            <p class="mb-0 text-muted">{{ transferTicket?.eventoNombre || 'Evento' }} · Disponibles: x{{ transferTicket?.cantidad || 0 }}</p>
          </div>

          <form class="row g-3 mt-1" @submit.prevent="submitTransferRequest">
            <div class="col-12 col-md-6">
              <label class="form-label">Nombre del destinatario</label>
              <input v-model.trim="transferDraft.recipientName" type="text" class="form-control" required />
            </div>
            <div class="col-12 col-md-6">
              <label class="form-label">Email del destinatario</label>
              <input v-model.trim="transferDraft.recipientEmail" type="email" class="form-control" required />
            </div>
            <div class="col-12 col-md-4">
              <label class="form-label">Cantidad a transferir</label>
              <input
                v-model.number="transferDraft.quantity"
                type="number"
                min="1"
                :max="transferTicket?.cantidad || 1"
                class="form-control"
                required
              />
            </div>
            <div class="col-12 col-md-8">
              <label class="form-label">Contrasena de seguridad</label>
              <input
                v-model="transferDraft.password"
                type="password"
                class="form-control"
                autocomplete="current-password"
                required
              />
            </div>
            <div class="col-12">
              <label class="form-label">Nota interna (opcional)</label>
              <textarea
                v-model.trim="transferDraft.notes"
                class="form-control"
                rows="2"
                placeholder="Motivo o detalle adicional para auditoria interna"
              ></textarea>
            </div>

            <div class="col-12">
              <div class="form-check secure-check">
                <input
                  id="transfer-confirm-modal"
                  v-model="transferDraft.confirmation"
                  class="form-check-input"
                  type="checkbox"
                />
                <label for="transfer-confirm-modal" class="form-check-label">
                  {{ transferButtonLabel }}
                </label>
              </div>
            </div>

            <div v-if="transferMessage.text" class="col-12">
              <div class="alert mb-0" :class="`alert-${transferMessage.type}`" role="alert">
                {{ transferMessage.text }}
              </div>
            </div>

            <div class="col-12 d-flex flex-wrap gap-2">
              <button class="btn btn-primary fw-semibold" type="submit" :disabled="transferSubmitting">
                {{ transferSubmitting ? 'Validando seguridad...' : 'Confirmar transferencia' }}
              </button>
              <button class="btn btn-outline-secondary fw-semibold" type="button" @click="closeTransferPanel">
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.user-dashboard-shell {
  border-radius: 1.25rem;
  border: 1px solid #dce4ec;
  background:
    radial-gradient(circle at 0% 0%, rgba(8, 145, 178, 0.09), transparent 46%),
    radial-gradient(circle at 100% 0%, rgba(255, 176, 0, 0.11), transparent 35%),
    #ffffff;
  padding: 1.2rem;
}

.dashboard-hero {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  border: 1px solid #dbe7f3;
  border-radius: 1rem;
  background: linear-gradient(120deg, #f7fbff, #ffffff);
  padding: 1rem;
}

.dashboard-identity {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.identity-badge {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  color: #0f172a;
  background: linear-gradient(145deg, #f59e0b, #fde68a);
  box-shadow: 0 12px 20px -16px rgba(245, 158, 11, 0.8);
}

.dashboard-kicker {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #0f4c5c;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.kpi-card {
  border: 1px solid #dbe7f3;
  border-radius: 0.95rem;
  background: #ffffff;
  padding: 0.9rem;
}

.kpi-label {
  margin: 0;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
  font-weight: 600;
}

.kpi-value {
  margin: 0.25rem 0;
  font-size: 1.25rem;
  line-height: 1.15;
  color: #0f172a;
  font-weight: 700;
}

.kpi-caption {
  margin: 0;
  font-size: 0.84rem;
  color: #64748b;
}

.account-tabs {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.account-tab {
  border: 1px solid #c6d7e7;
  border-radius: 999px;
  background: #f8fbff;
  color: #1e293b;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.45rem 0.95rem;
  transition: all 0.18s ease;
}

.account-tab:hover {
  border-color: #0f4c5c;
  color: #0f4c5c;
}

.account-tab-active {
  border-color: #0f4c5c;
  background: #0f4c5c;
  color: #ffffff;
}

.panel-loading {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.88rem;
  color: #0f4c5c;
}

.section-block {
  margin-top: 1rem;
  display: grid;
  gap: 0.75rem;
}

.section-card {
  border: 1px solid #dbe7f3;
  border-radius: 1rem;
  background: #ffffff;
  padding: 1rem;
}

.section-heading {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.8rem;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem;
}

.profile-row {
  border: 1px solid #e5edf5;
  border-radius: 0.85rem;
  background: #fbfdff;
  padding: 0.7rem 0.8rem;
}

.profile-label {
  color: #64748b;
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}

.profile-value {
  color: #0f172a;
  font-weight: 600;
  font-size: 0.95rem;
}

.security-list {
  margin: 0;
  padding-left: 1.1rem;
  color: #334155;
  display: grid;
  gap: 0.45rem;
}

.ticket-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.ticket-card {
  border: 1px solid #d6e4f0;
  border-radius: 0.95rem;
  background: linear-gradient(170deg, #ffffff, #f7fbff);
  padding: 0.85rem;
}

.ticket-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.7rem;
}

.ticket-kicker {
  color: #0f4c5c;
  font-size: 0.77rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}

.ticket-qty {
  border-radius: 999px;
  background: #0f4c5c;
  color: #ffffff;
  font-size: 0.74rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
}

.ticket-meta-grid {
  margin-top: 0.75rem;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.ticket-meta-grid-compact {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.meta-label {
  margin: 0;
  color: #64748b;
  font-size: 0.69rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}

.meta-value {
  margin: 0.15rem 0 0;
  color: #0f172a;
  font-size: 0.88rem;
  font-weight: 600;
}

.ticket-note {
  margin-top: 0.65rem;
  font-size: 0.84rem;
  color: #475569;
}

.transfer-hint {
  margin-top: 0.55rem;
  font-size: 0.78rem;
  color: #64748b;
}

.ticket-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 0.8rem;
}

.secure-check {
  border: 1px solid #8fa7bf;
  border-radius: 0.65rem;
  background: #d9e4ef;
  padding: 0.65rem 0.75rem 0.65rem 2.05rem;
}

.secure-check .form-check-label {
  color: #15263a;
}

.empty-state {
  border: 1px dashed #cad6e2;
  border-radius: 0.85rem;
  padding: 0.95rem;
  background: #fbfdff;
  color: #64748b;
}

.billing-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
}

.billing-card {
  border: 1px solid #deebf8;
  border-radius: 0.85rem;
  background: #ffffff;
  padding: 0.75rem;
}

.billing-card-highlight {
  border-color: #f7b731;
  background: linear-gradient(145deg, #fff9ec, #ffffff);
}

.billing-label {
  margin: 0;
  color: #64748b;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}

.billing-value {
  margin: 0.25rem 0 0;
  color: #0f172a;
  font-size: 0.95rem;
  font-weight: 700;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.22rem 0.62rem;
  font-size: 0.72rem;
  font-weight: 700;
}

.status-success {
  background: #dcfce7;
  color: #166534;
}

.status-warning {
  background: #fef3c7;
  color: #92400e;
}

.status-danger {
  background: #fee2e2;
  color: #991b1b;
}

.status-neutral {
  background: #e2e8f0;
  color: #334155;
}

.secure-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(15, 23, 42, 0.52);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.secure-modal {
  width: min(640px, 100%);
  border-radius: 1rem;
}

.secure-modal-kicker {
  color: #0f4c5c;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}

.transfer-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1250;
  background: rgba(2, 6, 23, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 1rem;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.transfer-modal {
  width: min(780px, 100%);
  max-height: calc(100dvh - 2rem);
  margin: auto 0;
  border-radius: 1.2rem;
  border: 1px solid #9eb1c5;
  background:
    radial-gradient(circle at 12% 8%, rgba(248, 180, 0, 0.16), transparent 34%),
    radial-gradient(circle at 88% 0%, rgba(14, 116, 144, 0.2), transparent 26%),
    linear-gradient(160deg, #dde5ee 0%, #ced9e5 58%, #c2cfdd 100%);
  box-shadow: 0 28px 68px -30px rgba(2, 6, 23, 0.74);
  overflow: hidden;
}

.transfer-modal .card-body {
  max-height: calc(100dvh - 2rem);
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.transfer-modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
}

.transfer-modal-kicker {
  color: #0b3f54;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}

.transfer-ticket-summary {
  border: 1px solid #8fa6bd;
  border-radius: 0.85rem;
  background: #ced8e4;
  padding: 0.75rem 0.85rem;
}

.transfer-modal :deep(h3) {
  color: #0f1f33;
}

.transfer-modal :deep(.text-muted) {
  color: #43586f !important;
}

.transfer-modal :deep(.form-label) {
  color: #1a2d42;
  font-weight: 600;
}

.transfer-modal :deep(.form-control) {
  background: #e6edf4;
  border-color: #9fb3c8;
  color: #122238;
}

.transfer-modal :deep(.form-control::placeholder) {
  color: #5b6e83;
}

.transfer-modal :deep(.form-control:focus) {
  background: #edf3f9;
  border-color: #4c7093;
  box-shadow: 0 0 0 0.2rem rgba(39, 88, 129, 0.2);
}

.transfer-modal :deep(.btn-outline-secondary) {
  border-color: #6f849b;
  color: #1b2d43;
  background: rgba(255, 255, 255, 0.46);
}

.transfer-modal :deep(.btn-outline-secondary:hover) {
  border-color: #203a56;
  background: #203a56;
  color: #ffffff;
}

@media (max-width: 991.98px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ticket-grid {
    grid-template-columns: 1fr;
  }

  .billing-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767.98px) {
  .user-dashboard-shell {
    padding: 0.85rem;
  }

  .profile-grid,
  .ticket-meta-grid,
  .ticket-meta-grid-compact,
  .billing-grid,
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .section-card {
    padding: 0.85rem;
  }

  .transfer-modal-head {
    flex-direction: column;
  }

  .transfer-modal-backdrop {
    padding: 0.75rem;
  }

  .transfer-modal {
    max-height: calc(100dvh - 1.5rem);
    border-radius: 1rem;
  }

  .transfer-modal .card-body {
    max-height: calc(100dvh - 1.5rem);
  }
}
</style>
