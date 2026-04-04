<script setup>
import { computed, ref } from 'vue'
import InternalPanelLayout from '../../../components/layout/InternalPanelLayout.vue'
import AppLoader from '../../../components/common/AppLoader.vue'
import { INDICATIVOS_POR_PAIS } from '../../../config/phoneCodes'
import { ROUTES } from '../../../config/routes'
import {
  ESTADOS_PEDIDO_ADMIN,
  actualizarEstadoPedidoAdmin,
  listarPedidosAdmin,
} from '../../../services/pedidosService'
import { construirEnlaceWhatsapp } from '../../../utils/whatsapp'

const PAGE_SIZE_OPTIONS = [10, 20, 50]
const PESTANIAS = ['pendientes', 'aceptados', 'rechazados']
const ESTADO_QUERY_PESTANIA = {
  pendientes: ESTADOS_PEDIDO_ADMIN.pendiente,
  aceptados: ESTADOS_PEDIDO_ADMIN.aceptado,
  rechazados: `${ESTADOS_PEDIDO_ADMIN.rechazado},fallido`,
}

const enlaces = [
  { label: 'Tickets', to: ROUTES.adminConfig },
  { label: 'Usuarios', to: ROUTES.adminUsuarios },
  { label: 'Pedidos', to: ROUTES.adminPedidos },
  { label: 'Métricas', to: ROUTES.adminMetricas },
]

function crearPaginacionInicial() {
  return {
    page: 1,
    pageSize: 10,
    hasMore: false,
    cargado: false,
  }
}

function crearEstadoPaginacionTabs() {
  return {
    pendientes: crearPaginacionInicial(),
    aceptados: crearPaginacionInicial(),
    rechazados: crearPaginacionInicial(),
  }
}

const pestañaActiva = ref('pendientes')
const filtroBusqueda = ref('')
const mensajeOperacion = ref('')
const mensajeOperacionTipo = ref('')
const actualizandoPorPedido = ref({})
const usuarioAsignacionPorPedido = ref({})
const pedidosPorPestaña = ref({
  pendientes: [],
  aceptados: [],
  rechazados: [],
})
const cargandoPorPestaña = ref({
  pendientes: false,
  aceptados: false,
  rechazados: false,
})
const cachePaginas = ref({
  pendientes: {},
  aceptados: {},
  rechazados: {},
})
const paginacionPorPestaña = ref(crearEstadoPaginacionTabs())

const claseMensajeOperacion = computed(() => {
  if (!mensajeOperacion.value) return ''
  return mensajeOperacionTipo.value === 'error' ? 'alert alert-warning' : 'alert alert-success'
})

const configuracionPestañaActiva = computed(() => {
  return paginacionPorPestaña.value[pestañaActiva.value] || crearPaginacionInicial()
})

const cargandoPedidos = computed(() => Boolean(cargandoPorPestaña.value[pestañaActiva.value]))
const pestañaActivaCargada = computed(() => Boolean(configuracionPestañaActiva.value.cargado))

const puedePaginaAnterior = computed(() => configuracionPestañaActiva.value.page > 1)
const puedePaginaSiguiente = computed(() => Boolean(configuracionPestañaActiva.value.hasMore))

const pedidosSeccionActiva = computed(() => {
  const base = pedidosPorPestaña.value[pestañaActiva.value] || []
  const consulta = normalizarTexto(filtroBusqueda.value)
  if (!consulta) return ordenarPedidosSegunPrioridad(pestañaActiva.value, base)

  const filtrados = base.filter((pedido) => {
    const candidato = [
      pedido.id,
      pedido.referencia,
      pedido.correo_electronico,
      pedido.nombre_completo,
      pedido.documento,
      pedido.pais,
      pedido.estado,
      pedido.telefono,
      pedido.usuario_id,
    ]
      .map((valor) => String(valor || ''))
      .join(' ')

    return normalizarTexto(candidato).includes(consulta)
  })

  return ordenarPedidosSegunPrioridad(pestañaActiva.value, filtrados)
})

const metricasPedidos = computed(() => {
  const pendientes = pedidosPorPestaña.value.pendientes.length
  const aceptados = pedidosPorPestaña.value.aceptados.length
  const rechazados = pedidosPorPestaña.value.rechazados.length

  return {
    total: pendientes + aceptados + rechazados,
    pendientes,
    aceptados,
    rechazados,
  }
})

function normalizarTexto(valor = '') {
  return String(valor)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function normalizarEstadoPedido(estado = '') {
  return String(estado || '').trim().toLowerCase()
}

function normalizarEnteroPositivo(valor, fallback) {
  const parsed = Number(valor)
  if (Number.isInteger(parsed) && parsed > 0) return parsed
  return fallback
}

function obtenerKeyPagina(page, pageSize) {
  return `${page}:${pageSize}`
}

function obtenerEtiquetaEstado(estado = '') {
  const valor = normalizarEstadoPedido(estado)
  if (valor === ESTADOS_PEDIDO_ADMIN.pendiente) return 'Pendiente'
  if (valor === ESTADOS_PEDIDO_ADMIN.aceptado) return 'Aceptado'
  if (valor === ESTADOS_PEDIDO_ADMIN.rechazado || valor === 'fallido') return 'Rechazado'
  return valor || 'Sin estado'
}

function obtenerClaseEstado(estado = '') {
  const valor = normalizarEstadoPedido(estado)
  if (valor === ESTADOS_PEDIDO_ADMIN.pendiente) return 'admin-pedido-estado admin-pedido-estado-pendiente'
  if (valor === ESTADOS_PEDIDO_ADMIN.aceptado) return 'admin-pedido-estado admin-pedido-estado-aceptado'
  return 'admin-pedido-estado admin-pedido-estado-rechazado'
}

function formatearDinero(valor) {
  const numero = Number(valor || 0)
  return numero.toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatearFecha(valor) {
  if (!valor) return 'Fecha no disponible'
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return 'Fecha no disponible'

  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(fecha)
}

function obtenerCantidadTicketsPedido(pedido) {
  return (pedido.detalles || []).reduce((acumulado, detalle) => {
    return acumulado + Number(detalle?.cantidad || 0)
  }, 0)
}

function obtenerNombreCategoriaDetalle(detalle) {
  if (detalle?.categoria?.nombre) return detalle.categoria.nombre
  return `Categoría #${detalle?.categoria_id || '-'}`
}

function limpiarMensajeOperacion() {
  mensajeOperacion.value = ''
  mensajeOperacionTipo.value = ''
}

function mostrarMensajeOperacion(texto, tipo = 'exito') {
  mensajeOperacion.value = texto
  mensajeOperacionTipo.value = tipo
}

function estaActualizandoPedido(pedidoId) {
  return Boolean(actualizandoPorPedido.value[pedidoId])
}

function setActualizandoPedido(pedidoId, valor) {
  actualizandoPorPedido.value = {
    ...actualizandoPorPedido.value,
    [pedidoId]: Boolean(valor),
  }
}

function setPedidosTab(tab, pedidos) {
  pedidosPorPestaña.value = {
    ...pedidosPorPestaña.value,
    [tab]: Array.isArray(pedidos) ? pedidos : [],
  }
}

function setCargandoTab(tab, valor) {
  cargandoPorPestaña.value = {
    ...cargandoPorPestaña.value,
    [tab]: Boolean(valor),
  }
}

function setPaginacionTab(tab, cambios) {
  paginacionPorPestaña.value = {
    ...paginacionPorPestaña.value,
    [tab]: {
      ...paginacionPorPestaña.value[tab],
      ...cambios,
    },
  }
}

function guardarCachePagina(tab, page, pageSize, pedidos, hasMore) {
  const key = obtenerKeyPagina(page, pageSize)
  const cacheTab = cachePaginas.value[tab] || {}
  cachePaginas.value = {
    ...cachePaginas.value,
    [tab]: {
      ...cacheTab,
      [key]: {
        pedidos: [...pedidos],
        hasMore: Boolean(hasMore),
      },
    },
  }
}

function obtenerCachePagina(tab, page, pageSize) {
  const key = obtenerKeyPagina(page, pageSize)
  return cachePaginas.value[tab]?.[key] || null
}

function limpiarCachePedidos() {
  cachePaginas.value = {
    pendientes: {},
    aceptados: {},
    rechazados: {},
  }
  pedidosPorPestaña.value = {
    pendientes: [],
    aceptados: [],
    rechazados: [],
  }

  const siguienteEstadoPaginacion = {}
  for (const tab of PESTANIAS) {
    const pageSize = paginacionPorPestaña.value[tab]?.pageSize || 10
    siguienteEstadoPaginacion[tab] = {
      page: 1,
      pageSize,
      hasMore: false,
      cargado: false,
    }
  }
  paginacionPorPestaña.value = siguienteEstadoPaginacion
}

function ordenarPedidosSegunPrioridad(tab, pedidos) {
  const clon = [...(pedidos || [])]

  if (tab === 'aceptados') {
    clon.sort((a, b) => {
      const completoA = Number(a?.usuario_id || 0) > 0 ? 1 : 0
      const completoB = Number(b?.usuario_id || 0) > 0 ? 1 : 0
      if (completoA !== completoB) return completoA - completoB
      return Number(b?.id || 0) - Number(a?.id || 0)
    })
    return clon
  }

  clon.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0))
  return clon
}

function formatearConteoPestaña(tab) {
  const estado = paginacionPorPestaña.value[tab]
  if (!estado?.cargado) return '-'
  return String((pedidosPorPestaña.value[tab] || []).length)
}

function valorAsignacionUsuario(pedido) {
  const llavePedido = String(pedido?.id || '')
  if (!llavePedido) return ''

  if (Object.prototype.hasOwnProperty.call(usuarioAsignacionPorPedido.value, llavePedido)) {
    return usuarioAsignacionPorPedido.value[llavePedido]
  }

  return pedido?.usuario_id ? String(pedido.usuario_id) : ''
}

function actualizarValorAsignacionUsuario(pedidoId, valor) {
  const llavePedido = String(pedidoId || '')
  if (!llavePedido) return

  usuarioAsignacionPorPedido.value = {
    ...usuarioAsignacionPorPedido.value,
    [llavePedido]: String(valor || '').replace(/[^0-9]/g, ''),
  }
}

function esUsuarioIdValido(valor) {
  const parsed = Number(String(valor || '').trim())
  return Number.isInteger(parsed) && parsed > 0
}

function normalizarPaisTexto(valor = '') {
  return String(valor || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function obtenerIndicativoPais(pais) {
  const valor = normalizarPaisTexto(pais)
  if (!valor) return null
  return INDICATIVOS_POR_PAIS[valor] || null
}

function telefonoWhatsAppInternacional(telefono, pais = '') {
  const raw = String(telefono || '').trim()
  if (!raw) return null

  let sanitizado = raw.replace(/[^\d+]/g, '').replace(/(?!^)\+/g, '')
  if (sanitizado.startsWith('00')) {
    sanitizado = `+${sanitizado.slice(2)}`
  }

  const digitos = sanitizado.replace(/\D/g, '')
  if (!digitos) return null

  if (sanitizado.startsWith('+')) {
    if (!/^[1-9]\d{7,14}$/.test(digitos)) return null
    return digitos
  }

  const indicativo = obtenerIndicativoPais(pais)
  if (indicativo) {
    const combinado = `${indicativo}${digitos}`
    if (/^[1-9]\d{7,14}$/.test(combinado)) {
      return combinado
    }
  }

  if (/^[1-9]\d{10,14}$/.test(digitos)) {
    return digitos
  }

  if (digitos.length === 10) {
    return `57${digitos}`
  }

  return null
}

function telefonoPedidoValido(pedido) {
  return Boolean(telefonoWhatsAppInternacional(pedido?.telefono, pedido?.pais))
}

function mensajeWhatsappPedido(pedido) {
  return [
    'Hola, acabo de revisar tu pedido.',
    '',
    'Detalles:',
    `- ID: ${pedido?.id ?? '-'}`,
    `- Referencia: ${pedido?.referencia || '-'}`,
    '',
    'Te contacto para continuar con el proceso.',
  ].join('\n')
}

function enlaceWhatsappPedido(pedido) {
  const telefono = telefonoWhatsAppInternacional(pedido?.telefono, pedido?.pais)
  if (!telefono) return ''

  return construirEnlaceWhatsapp(telefono, mensajeWhatsappPedido(pedido))
}

function abrirWhatsappPedido(pedido) {
  const enlace = enlaceWhatsappPedido(pedido)
  if (!enlace || typeof window === 'undefined') return
  window.open(enlace, '_blank', 'noopener,noreferrer')
}

async function cargarPedidosPestaña(tab, { force = false, page = null, pageSize = null } = {}) {
  const config = paginacionPorPestaña.value[tab] || crearPaginacionInicial()
  const targetPage = normalizarEnteroPositivo(page ?? config.page, 1)
  const targetPageSize = normalizarEnteroPositivo(pageSize ?? config.pageSize, 10)

  const cache = !force ? obtenerCachePagina(tab, targetPage, targetPageSize) : null
  if (cache) {
    setPedidosTab(tab, cache.pedidos)
    setPaginacionTab(tab, {
      page: targetPage,
      pageSize: targetPageSize,
      hasMore: Boolean(cache.hasMore),
      cargado: true,
    })
    return
  }

  setCargandoTab(tab, true)
  try {
    const skip = (targetPage - 1) * targetPageSize
    const rows = await listarPedidosAdmin({
      skip,
      limit: targetPageSize + 1,
      estado: ESTADO_QUERY_PESTANIA[tab],
    })

    const hasMore = rows.length > targetPageSize
    const pedidosPagina = ordenarPedidosSegunPrioridad(tab, rows.slice(0, targetPageSize))

    for (const pedido of pedidosPagina) {
      const llave = String(pedido.id || '')
      if (!llave) continue
      if (!Object.prototype.hasOwnProperty.call(usuarioAsignacionPorPedido.value, llave)) {
        usuarioAsignacionPorPedido.value = {
          ...usuarioAsignacionPorPedido.value,
          [llave]: pedido.usuario_id ? String(pedido.usuario_id) : '',
        }
      }
    }

    setPedidosTab(tab, pedidosPagina)
    setPaginacionTab(tab, {
      page: targetPage,
      pageSize: targetPageSize,
      hasMore,
      cargado: true,
    })
    guardarCachePagina(tab, targetPage, targetPageSize, pedidosPagina, hasMore)
  } catch (error) {
    mostrarMensajeOperacion(error?.message || 'No fue posible cargar los pedidos.', 'error')
  } finally {
    setCargandoTab(tab, false)
  }
}

async function seleccionarPestaña(tab) {
  pestañaActiva.value = tab
  if (!paginacionPorPestaña.value[tab]?.cargado) {
    await cargarPedidosPestaña(tab)
  }
}

async function cargarPestañaActiva({ force = false } = {}) {
  limpiarMensajeOperacion()
  await cargarPedidosPestaña(pestañaActiva.value, { force })
}

async function cambiarPaginaActiva(delta) {
  const config = configuracionPestañaActiva.value
  await cargarPedidosPestaña(pestañaActiva.value, {
    page: config.page + delta,
    pageSize: config.pageSize,
  })
}

async function cambiarTamanoPaginaActiva(event) {
  const nuevoTamano = Number(event?.target?.value || configuracionPestañaActiva.value.pageSize)
  await cargarPedidosPestaña(pestañaActiva.value, {
    page: 1,
    pageSize: normalizarEnteroPositivo(nuevoTamano, 10),
  })
}

async function recargarTrasMutacion() {
  limpiarCachePedidos()
  await cargarPedidosPestaña(pestañaActiva.value, {
    force: true,
    page: 1,
    pageSize: configuracionPestañaActiva.value.pageSize,
  })
}

async function actualizarEstadoPedidoConFeedback({
  pedido,
  estado,
  usuarioId = null,
  mensajeExito,
  mensajeError,
}) {
  if (!pedido?.id) return

  setActualizandoPedido(pedido.id, true)
  limpiarMensajeOperacion()

  try {
    await actualizarEstadoPedidoAdmin({
      pedidoId: pedido.id,
      estado,
      usuarioId,
    })
    await recargarTrasMutacion()
    mostrarMensajeOperacion(mensajeExito)
  } catch (error) {
    mostrarMensajeOperacion(error?.message || mensajeError, 'error')
  } finally {
    setActualizandoPedido(pedido.id, false)
  }
}

async function marcarPedidoRechazado(pedido) {
  return actualizarEstadoPedidoConFeedback({
    pedido,
    estado: ESTADOS_PEDIDO_ADMIN.rechazado,
    mensajeExito: `Pedido #${pedido.id} movido a rechazados correctamente.`,
    mensajeError: 'No fue posible mover el pedido a rechazados.',
  })
}

async function marcarPedidoAceptado(pedido) {
  return actualizarEstadoPedidoConFeedback({
    pedido,
    estado: ESTADOS_PEDIDO_ADMIN.aceptado,
    mensajeExito: `Pedido #${pedido.id} movido a aceptados correctamente.`,
    mensajeError: 'No fue posible mover el pedido a aceptados.',
  })
}

async function moverPedidoAPendientes(pedido) {
  return actualizarEstadoPedidoConFeedback({
    pedido,
    estado: ESTADOS_PEDIDO_ADMIN.pendiente,
    mensajeExito: `Pedido #${pedido.id} movido a pendientes correctamente.`,
    mensajeError: 'No fue posible mover el pedido a pendientes.',
  })
}

async function aceptarYAsignarPedidoPendiente(pedido) {
  const usuarioValor = valorAsignacionUsuario(pedido)
  if (!esUsuarioIdValido(usuarioValor)) {
    mostrarMensajeOperacion('Debes ingresar un ID de usuario válido para aceptar el pedido.', 'error')
    return
  }

  const usuarioId = Number(usuarioValor)
  return actualizarEstadoPedidoConFeedback({
    pedido,
    estado: ESTADOS_PEDIDO_ADMIN.aceptado,
    usuarioId,
    mensajeExito: `Pedido #${pedido.id} aceptado y asignado al usuario #${usuarioId}.`,
    mensajeError: 'No fue posible aceptar y asignar el pedido.',
  })
}

async function guardarAsignacionPedidoAceptado(pedido) {
  if (!pedido?.id) return

  const usuarioValor = valorAsignacionUsuario(pedido)
  if (!esUsuarioIdValido(usuarioValor)) {
    mostrarMensajeOperacion('Ingresa un ID de usuario válido para asignar tickets.', 'error')
    return
  }

  const usuarioId = Number(usuarioValor)
  const usuarioActual = Number(pedido.usuario_id || 0)
  if (usuarioActual > 0 && usuarioActual === usuarioId) {
    mostrarMensajeOperacion(`El pedido #${pedido.id} ya está asignado al usuario #${usuarioId}.`)
    return
  }

  return actualizarEstadoPedidoConFeedback({
    pedido,
    estado: ESTADOS_PEDIDO_ADMIN.aceptado,
    usuarioId,
    mensajeExito:
      usuarioActual > 0
        ? `Tickets del pedido #${pedido.id} reasignados al usuario #${usuarioId}.`
        : `Tickets del pedido #${pedido.id} asignados al usuario #${usuarioId}.`,
    mensajeError: 'No fue posible guardar la asignación de tickets.',
  })
}
</script>

<template>
  <InternalPanelLayout
    title="Configuración de pedidos"
    subtitle="Carga por pestaña, paginación y acciones compactas para procesar pedidos sin saturar la API."
    :links="enlaces"
  >
    <div class="col-12">
      <section class="admin-toolbar mb-3">
        <div>
          <p class="admin-toolbar-kicker mb-1">Admin / Configuración / Pedidos</p>
          <h2 class="h5 fw-bold mb-0">Panel de pedidos</h2>
        </div>
        <button class="btn btn-primary" type="button" :disabled="cargandoPedidos" @click="cargarPestañaActiva({ force: pestañaActivaCargada })">
          {{ cargandoPedidos ? 'Cargando...' : pestañaActivaCargada ? 'Actualizar pestaña' : 'Cargar pedidos' }}
        </button>
      </section>

      <section class="admin-filters-panel mb-3">
        <div class="row g-2 align-items-end">
          <div class="col-12 col-lg-5">
            <label class="form-label fw-semibold small text-uppercase mb-1">Buscar en la página</label>
            <input
              v-model.trim="filtroBusqueda"
              class="form-control admin-control"
              type="text"
              placeholder="ID, referencia, nombre, correo, documento..."
            />
          </div>
          <div class="col-12 col-lg-3">
            <label class="form-label fw-semibold small text-uppercase mb-1">Items por página</label>
            <select class="form-select admin-control" :value="configuracionPestañaActiva.pageSize" @change="cambiarTamanoPaginaActiva">
              <option v-for="size in PAGE_SIZE_OPTIONS" :key="size" :value="size">{{ size }}</option>
            </select>
          </div>
          <div class="col-12 col-lg-4">
            <label class="form-label fw-semibold small text-uppercase mb-1">Sección</label>
            <div class="admin-pedidos-tabs">
              <button
                type="button"
                class="admin-pedidos-tab"
                :class="{ 'admin-pedidos-tab-activa': pestañaActiva === 'pendientes' }"
                @click="seleccionarPestaña('pendientes')"
              >
                Pendientes ({{ formatearConteoPestaña('pendientes') }})
              </button>
              <button
                type="button"
                class="admin-pedidos-tab"
                :class="{ 'admin-pedidos-tab-activa': pestañaActiva === 'aceptados' }"
                @click="seleccionarPestaña('aceptados')"
              >
                Aceptados ({{ formatearConteoPestaña('aceptados') }})
              </button>
              <button
                type="button"
                class="admin-pedidos-tab"
                :class="{ 'admin-pedidos-tab-activa': pestañaActiva === 'rechazados' }"
                @click="seleccionarPestaña('rechazados')"
              >
                Rechazados ({{ formatearConteoPestaña('rechazados') }})
              </button>
            </div>
          </div>
        </div>

        <div class="admin-metrics-grid mt-3">
          <article class="admin-metric-card">
            <p class="admin-metric-label mb-1">Total cargado</p>
            <p class="admin-metric-value mb-0">{{ metricasPedidos.total }}</p>
          </article>
          <article class="admin-metric-card">
            <p class="admin-metric-label mb-1">Pendientes</p>
            <p class="admin-metric-value mb-0">{{ metricasPedidos.pendientes }}</p>
          </article>
          <article class="admin-metric-card">
            <p class="admin-metric-label mb-1">Aceptados</p>
            <p class="admin-metric-value mb-0">{{ metricasPedidos.aceptados }}</p>
          </article>
          <article class="admin-metric-card">
            <p class="admin-metric-label mb-1">Rechazados</p>
            <p class="admin-metric-value mb-0">{{ metricasPedidos.rechazados }}</p>
          </article>
        </div>
      </section>

      <div v-if="mensajeOperacion" :class="claseMensajeOperacion" role="alert">
        <p class="mb-0">{{ mensajeOperacion }}</p>
      </div>

      <div v-if="cargandoPedidos" class="admin-loading-box">
        <AppLoader variant="skeleton-cards" :count="3" />
      </div>

      <div v-else-if="!pestañaActivaCargada" class="empty-state-admin">
        <p class="mb-0">Selecciona una pestaña y presiona “Cargar pedidos” para consultar solo esa sección.</p>
      </div>

      <div v-else class="d-grid gap-2">
        <article
          v-for="pedido in pedidosSeccionActiva"
          :key="pedido.id"
          class="admin-card admin-pedido-card admin-pedido-card-compact"
        >
          <div class="admin-card-body admin-pedido-body-compact">
            <header class="admin-pedido-header-compact">
              <div class="admin-pedido-meta-inline">
                <span class="admin-pedido-pill">ID #{{ pedido.id }}</span>
                <span class="admin-pedido-pill">Ref {{ pedido.referencia || 'Sin referencia' }}</span>
                <span class="admin-pedido-pill">{{ formatearFecha(pedido.fecha_creacion) }}</span>
              </div>
              <span :class="obtenerClaseEstado(pedido.estado)">{{ obtenerEtiquetaEstado(pedido.estado) }}</span>
            </header>

            <div class="admin-pedido-resumen-grid admin-pedido-resumen-grid-compact">
              <div>
                <p class="admin-pedido-etiqueta mb-0">Cliente</p>
                <p class="mb-0 fw-semibold text-truncate">{{ pedido.nombre_completo || 'Sin nombre' }}</p>
              </div>
              <div>
                <p class="admin-pedido-etiqueta mb-0">Documento</p>
                <p class="mb-0 fw-semibold">{{ pedido.documento || 'Sin documento' }}</p>
              </div>
              <div>
                <p class="admin-pedido-etiqueta mb-0">Teléfono</p>
                <p class="mb-0 fw-semibold">{{ pedido.telefono || 'Sin teléfono' }}</p>
              </div>
              <div>
                <p class="admin-pedido-etiqueta mb-0">Total</p>
                <p class="mb-0 fw-semibold">{{ formatearDinero(pedido.total) }} USD</p>
              </div>
            </div>

            <div class="admin-pedido-detalles admin-pedido-detalles-compact">
              <ul class="mb-0">
                <li v-for="detalle in pedido.detalles || []" :key="detalle.id || `${pedido.id}-${detalle.categoria_id}`">
                  {{ obtenerNombreCategoriaDetalle(detalle) }} · {{ detalle.cantidad }} · {{ formatearDinero(detalle.precio_unitario) }} USD
                </li>
              </ul>
            </div>

            <div
              v-if="pestañaActiva === 'pendientes'"
              class="admin-pedido-acciones admin-pedido-acciones-compact admin-pedido-acciones-pendientes"
            >
              <button
                type="button"
                class="btn btn-success"
                :disabled="!telefonoPedidoValido(pedido) || estaActualizandoPedido(pedido.id)"
                @click="abrirWhatsappPedido(pedido)"
              >
                WhatsApp
              </button>
              <button
                type="button"
                class="btn btn-outline-danger"
                :disabled="estaActualizandoPedido(pedido.id)"
                @click="marcarPedidoRechazado(pedido)"
              >
                Rechazar
              </button>
              <input
                class="form-control admin-control"
                type="text"
                inputmode="numeric"
                placeholder="ID usuario"
                :value="valorAsignacionUsuario(pedido)"
                :disabled="estaActualizandoPedido(pedido.id)"
                @input="(event) => actualizarValorAsignacionUsuario(pedido.id, event.target.value)"
              />
              <button
                type="button"
                class="btn btn-primary"
                :disabled="!esUsuarioIdValido(valorAsignacionUsuario(pedido)) || estaActualizandoPedido(pedido.id)"
                @click="aceptarYAsignarPedidoPendiente(pedido)"
              >
                {{ estaActualizandoPedido(pedido.id) ? 'Procesando...' : 'Aceptar y asignar' }}
              </button>
            </div>

            <div
              v-if="pestañaActiva === 'aceptados'"
              class="admin-pedido-acciones admin-pedido-acciones-compact admin-pedido-acciones-aceptados"
            >
              <button
                type="button"
                class="btn btn-success"
                :disabled="!telefonoPedidoValido(pedido) || estaActualizandoPedido(pedido.id)"
                @click="abrirWhatsappPedido(pedido)"
              >
                WhatsApp
              </button>
              <button
                type="button"
                class="btn btn-outline-secondary"
                :disabled="estaActualizandoPedido(pedido.id)"
                @click="moverPedidoAPendientes(pedido)"
              >
                Mover a pendientes
              </button>
              <button
                type="button"
                class="btn btn-outline-danger"
                :disabled="estaActualizandoPedido(pedido.id)"
                @click="marcarPedidoRechazado(pedido)"
              >
                Mover a rechazados
              </button>
              <input
                class="form-control admin-control"
                type="text"
                inputmode="numeric"
                placeholder="ID usuario"
                :value="valorAsignacionUsuario(pedido)"
                :disabled="estaActualizandoPedido(pedido.id)"
                @input="(event) => actualizarValorAsignacionUsuario(pedido.id, event.target.value)"
              />
              <button
                type="button"
                class="btn btn-primary"
                :disabled="!esUsuarioIdValido(valorAsignacionUsuario(pedido)) || estaActualizandoPedido(pedido.id)"
                @click="guardarAsignacionPedidoAceptado(pedido)"
              >
                {{ estaActualizandoPedido(pedido.id) ? 'Guardando...' : 'Guardar asignación' }}
              </button>
            </div>

            <div
              v-if="pestañaActiva === 'rechazados'"
              class="admin-pedido-acciones admin-pedido-acciones-compact admin-pedido-acciones-rechazados"
            >
              <button
                type="button"
                class="btn btn-success"
                :disabled="!telefonoPedidoValido(pedido) || estaActualizandoPedido(pedido.id)"
                @click="abrirWhatsappPedido(pedido)"
              >
                WhatsApp
              </button>
              <button
                type="button"
                class="btn btn-outline-secondary"
                :disabled="estaActualizandoPedido(pedido.id)"
                @click="moverPedidoAPendientes(pedido)"
              >
                Mover a pendientes
              </button>
              <button
                type="button"
                class="btn btn-primary"
                :disabled="estaActualizandoPedido(pedido.id)"
                @click="marcarPedidoAceptado(pedido)"
              >
                {{ estaActualizandoPedido(pedido.id) ? 'Procesando...' : 'Mover a aceptados' }}
              </button>
            </div>
          </div>
        </article>

        <div v-if="!pedidosSeccionActiva.length" class="empty-state-admin">
          <p class="mb-0">No hay pedidos en esta sección con el filtro actual.</p>
        </div>

        <section class="admin-pagination mt-2">
          <button
            class="btn btn-outline-light"
            type="button"
            :disabled="!puedePaginaAnterior || cargandoPedidos"
            @click="cambiarPaginaActiva(-1)"
          >
            Anterior
          </button>
          <p class="admin-pagination-label mb-0">Página {{ configuracionPestañaActiva.page }}</p>
          <button
            class="btn btn-outline-light"
            type="button"
            :disabled="!puedePaginaSiguiente || cargandoPedidos"
            @click="cambiarPaginaActiva(1)"
          >
            Siguiente
          </button>
        </section>
      </div>
    </div>
  </InternalPanelLayout>
</template>
