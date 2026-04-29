<script setup>
import { computed, reactive, ref } from 'vue'
import InternalPanelLayout from '../../../components/layout/InternalPanelLayout.vue'
import AppLoader from '../../../components/common/AppLoader.vue'
import { ROUTES } from '../../../config/routes'
import { obtenerMetricasPedidosAdmin } from '../../../services/pedidosService'

const RANGO_OPTIONS = [
  { value: '7d', label: 'Ultimos 7 dias' },
  { value: '30d', label: 'Ultimos 30 dias' },
  { value: '90d', label: 'Ultimos 90 dias' },
  { value: '180d', label: 'Ultimos 180 dias' },
  { value: '365d', label: 'Ultimos 365 dias' },
  { value: 'mtd', label: 'Mes actual (MTD)' },
  { value: 'qtd', label: 'Trimestre actual (QTD)' },
  { value: 'ytd', label: 'Ano actual (YTD)' },
  { value: 'all', label: 'Historico completo' },
  { value: 'custom', label: 'Rango personalizado' },
]

const RANGO_LABEL_MAP = Object.fromEntries(RANGO_OPTIONS.map((option) => [option.value, option.label]))

const GROUP_BY_OPTIONS = [
  { value: 'day', label: 'Diario' },
  { value: 'week', label: 'Semanal' },
  { value: 'month', label: 'Mensual' },
]

const GROUP_BY_LABEL_MAP = Object.fromEntries(GROUP_BY_OPTIONS.map((option) => [option.value, option.label]))

const ESTADO_OPTIONS = [
  { value: 'pendiente', label: 'Pendiente' },
  { value: 'pagado', label: 'Pagado' },
  { value: 'cancelado', label: 'Cancelado' },
  { value: 'fallido', label: 'Fallido' },
]

const links = [
  { label: 'Tickets', to: ROUTES.adminConfig },
  { label: 'Usuarios', to: ROUTES.adminUsuarios },
  { label: 'Pedidos', to: ROUTES.adminPedidos },
  { label: 'Metricas', to: ROUTES.adminMetricas },
]

function createDefaultFilters() {
  return {
    rango: '30d',
    fecha_desde: '',
    fecha_hasta: '',
    group_by: 'day',
    estados: {
      pendiente: true,
      pagado: true,
      cancelado: true,
      fallido: true,
    },
    paises: [],
    paises_manual: '',
    min_total: '',
    max_total: '',
    top_n: 8,
    ventas_solo_aprobadas: true,
    producto_ids: '',
    categoria_ids: '',
  }
}

const filtros = reactive(createDefaultFilters())
const mostrarSubfiltros = ref(false)

const cargando = ref(false)
const metricas = ref(null)
const error = ref('')
const hasLoaded = ref(false)

function toNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function formatMoney(value) {
  return `${toNumber(value).toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} USD`
}

function formatPercent(value) {
  return `${toNumber(value).toLocaleString('es-CO', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`
}

function formatInteger(value) {
  const normalized = Math.max(0, Math.trunc(toNumber(value)))
  return normalized.toLocaleString('es-CO')
}

function formatDateTime(value) {
  if (!value) return 'Sin fecha'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Sin fecha'
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function toIsoDateStart(value) {
  if (!value) return null
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString()
}

function toIsoDateEnd(value) {
  if (!value) return null
  const date = new Date(`${value}T23:59:59`)
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString()
}

function normalizeTextList(raw) {
  if (!raw) return []

  const source = Array.isArray(raw)
    ? raw
    : String(raw)
        .split(',')
        .map((item) => item.trim())

  const unique = []
  const seen = new Set()

  for (const item of source) {
    const value = String(item || '').trim().toLowerCase()
    if (!value || seen.has(value)) continue
    seen.add(value)
    unique.push(value)
  }

  return unique
}

function estadosSeleccionados() {
  return ESTADO_OPTIONS.filter((item) => Boolean(filtros.estados[item.value])).map((item) => item.value)
}

function construirPayloadFiltros() {
  const estado = estadosSeleccionados()
  if (!estado.length) {
    throw new Error('Selecciona al menos un estado para el analisis')
  }

  const pais = normalizeTextList([...filtros.paises, ...normalizeTextList(filtros.paises_manual)])

  const payload = {
    rango: filtros.rango,
    group_by: filtros.group_by,
    estado,
    pais,
    min_total: filtros.min_total,
    max_total: filtros.max_total,
    top_n: filtros.top_n,
    ventas_solo_aprobadas: filtros.ventas_solo_aprobadas,
    producto_ids: filtros.producto_ids,
    categoria_ids: filtros.categoria_ids,
  }

  if (filtros.rango === 'custom') {
    payload.fecha_desde = toIsoDateStart(filtros.fecha_desde)
    payload.fecha_hasta = toIsoDateEnd(filtros.fecha_hasta)

    if (!payload.fecha_desde || !payload.fecha_hasta) {
      throw new Error('Para rango personalizado debes seleccionar fecha desde y fecha hasta')
    }
  }

  return payload
}

async function cargarMetricas({ force = false } = {}) {
  cargando.value = true
  error.value = ''

  try {
    const payload = construirPayloadFiltros()
    metricas.value = await obtenerMetricasPedidosAdmin(payload, { force })
    hasLoaded.value = true
  } catch (err) {
    error.value = err?.message || 'No fue posible cargar las metricas del panel'
  } finally {
    cargando.value = false
  }
}

function aplicarFiltros() {
  cargarMetricas({ force: hasLoaded.value })
}

function limpiarFiltros() {
  const defaults = createDefaultFilters()
  Object.assign(filtros, defaults)

  if (!hasLoaded.value) {
    error.value = ''
    metricas.value = null
    return
  }

  cargarMetricas({ force: true })
}

function toggleEstado(estado) {
  filtros.estados[estado] = !filtros.estados[estado]
}

function togglePaisSugerido(pais) {
  const normalized = String(pais || '').trim().toLowerCase()
  if (!normalized) return

  if (filtros.paises.includes(normalized)) {
    filtros.paises = filtros.paises.filter((item) => item !== normalized)
    return
  }

  filtros.paises = [...filtros.paises, normalized]
}

function isPaisSeleccionado(pais) {
  return filtros.paises.includes(String(pais || '').trim().toLowerCase())
}

const resumen = computed(() => metricas.value?.resumen || null)
const visitantes = computed(() => metricas.value?.visitantes || null)
const estadoBreakdown = computed(() => metricas.value?.estado_breakdown || [])
const tendencia = computed(() => metricas.value?.tendencia || [])
const topProductos = computed(() => metricas.value?.top_productos || [])
const topCategorias = computed(() => metricas.value?.top_categorias || [])
const topPaises = computed(() => metricas.value?.top_paises || [])

const sugerenciasPaises = computed(() => {
  const raw = topPaises.value.map((item) => String(item.pais || '').trim().toLowerCase()).filter(Boolean)
  return [...new Set(raw)].slice(0, 10)
})

const performanceInfo = computed(() => metricas.value?.performance || null)
const ultimaActualizacion = computed(() => {
  if (!performanceInfo.value?.generated_at) return 'Sin datos'
  return formatDateTime(performanceInfo.value.generated_at)
})

const donutSlices = computed(() => {
  const totalGenerado = toNumber(resumen.value?.total_generado)
  const totalPendiente = toNumber(resumen.value?.total_pendiente)
  const totalRechazado = toNumber(resumen.value?.total_rechazado)
  const total = totalGenerado + totalPendiente + totalRechazado

  return {
    total,
    generado: totalGenerado,
    pendiente: totalPendiente,
    rechazado: totalRechazado,
  }
})

const donutStyle = computed(() => {
  const total = donutSlices.value.total
  if (total <= 0) {
    return {
      background:
        'conic-gradient(rgba(46, 125, 255, 0.2) 0 33%, rgba(232, 191, 106, 0.2) 33% 66%, rgba(255, 74, 61, 0.2) 66% 100%)',
    }
  }

  const pctGenerado = (donutSlices.value.generado / total) * 100
  const pctPendiente = (donutSlices.value.pendiente / total) * 100
  const corte1 = pctGenerado
  const corte2 = pctGenerado + pctPendiente

  return {
    background: `conic-gradient(#2e7dff 0 ${corte1}%, #e8bf6a ${corte1}% ${corte2}%, #ff4a3d ${corte2}% 100%)`,
  }
})

const donutLegend = computed(() => {
  const total = donutSlices.value.total || 1
  return [
    {
      label: 'Generado',
      color: '#2e7dff',
      amount: donutSlices.value.generado,
      share: (donutSlices.value.generado / total) * 100,
    },
    {
      label: 'Pendiente',
      color: '#e8bf6a',
      amount: donutSlices.value.pendiente,
      share: (donutSlices.value.pendiente / total) * 100,
    },
    {
      label: 'Rechazado',
      color: '#ff4a3d',
      amount: donutSlices.value.rechazado,
      share: (donutSlices.value.rechazado / total) * 100,
    },
  ]
})

const tendenciaVisible = computed(() => {
  if (tendencia.value.length <= 24) return tendencia.value
  return tendencia.value.slice(-24)
})

const tendenciaMax = computed(() => {
  if (!tendenciaVisible.value.length) return 1
  return Math.max(...tendenciaVisible.value.map((item) => toNumber(item.total_generado)), 1)
})

const topProductosMaxUnidades = computed(() => {
  if (!topProductos.value.length) return 1
  return Math.max(...topProductos.value.map((item) => toNumber(item.unidades)), 1)
})

const topCategoriasMaxIngresos = computed(() => {
  if (!topCategorias.value.length) return 1
  return Math.max(...topCategorias.value.map((item) => toNumber(item.ingresos)), 1)
})

const rangoActivoLabel = computed(() => {
  if (filtros.rango === 'custom') {
    const fechaDesde = filtros.fecha_desde || 'sin inicio'
    const fechaHasta = filtros.fecha_hasta || 'sin cierre'
    return `${fechaDesde} a ${fechaHasta}`
  }

  return RANGO_LABEL_MAP[filtros.rango] || filtros.rango
})

const estadosActivosLabel = computed(() => {
  const labels = ESTADO_OPTIONS
    .filter((item) => Boolean(filtros.estados[item.value]))
    .map((item) => item.label)

  return labels.length ? labels.join(', ') : 'Ninguno'
})

const filtroContextoItems = computed(() => [
  `Rango: ${rangoActivoLabel.value}`,
  `Agrupacion: ${GROUP_BY_LABEL_MAP[filtros.group_by] || filtros.group_by}`,
  `Estados: ${estadosActivosLabel.value}`,
  `Top N: ${filtros.top_n}`,
])

const kpiCards = computed(() => {
  if (!resumen.value) return []

  return [
    {
      key: 'total_generado',
      label: 'Total generado',
      value: formatMoney(resumen.value.total_generado),
      caption: 'Ingresos confirmados en el periodo',
      tone: 'money',
    },
    {
      key: 'total_pendiente',
      label: 'Dinero pendiente',
      value: formatMoney(resumen.value.total_pendiente),
      caption: 'Pagos aun no liquidados',
      tone: 'pending',
    },
    {
      key: 'total_rechazado',
      label: 'Dinero rechazado',
      value: formatMoney(resumen.value.total_rechazado),
      caption: 'Transacciones fallidas o canceladas',
      tone: 'risk',
    },
    {
      key: 'tasa_aprobacion',
      label: 'Tasa de aprobacion',
      value: formatPercent(resumen.value.tasa_aprobacion),
      caption: 'Efectividad del proceso de pago',
      tone: 'efficiency',
    },
    {
      key: 'ticket_promedio_pagado',
      label: 'Ticket promedio pagado',
      value: formatMoney(resumen.value.ticket_promedio_pagado),
      caption: 'Valor medio por pedido aprobado',
      tone: 'money',
    },
    {
      key: 'unidades_vendidas',
      label: 'Unidades vendidas',
      value: formatInteger(resumen.value.unidades_vendidas),
      caption: 'Volumen total de productos vendidos',
      tone: 'efficiency',
    },
    {
      key: 'visitantes_unicos',
      label: 'Visitantes unicos (aprox)',
      value: formatInteger(visitantes.value?.visitantes_unicos_aprox),
      caption: 'Audiencia acumulada para este rango',
      tone: 'traffic',
    },
    {
      key: 'total_visitas',
      label: 'Visitas registradas',
      value: formatInteger(visitantes.value?.total_visitas),
      caption: 'Eventos de visita aceptados por API',
      tone: 'traffic',
    },
    {
      key: 'visitantes_hoy',
      label: 'Visitantes hoy (aprox)',
      value: formatInteger(visitantes.value?.visitantes_hoy_aprox),
      caption: 'Pulso diario de adquisicion',
      tone: 'traffic',
    },
  ]
})
</script>

<template>
  <InternalPanelLayout
    title="Metricas del negocio"
    subtitle="Dashboard ejecutivo tipo BI con agregaciones optimizadas y filtros avanzados."
    :links="links"
  >
    <div class="col-12 admin-metricas-page">
      <section class="admin-toolbar mb-2">
        <div>
          <p class="admin-toolbar-kicker mb-1">Admin / Configuracion / Metricas</p>
          <h2 class="h5 fw-bold mb-0">Performance comercial en tiempo real</h2>
        </div>
        <div class="d-flex flex-wrap gap-2">
          <button class="btn btn-primary" type="button" :disabled="cargando" @click="cargarMetricas({ force: hasLoaded })">
            {{ cargando ? 'Cargando...' : hasLoaded ? 'Actualizar datos' : 'Cargar metricas' }}
          </button>
        </div>
      </section>

      <section class="admin-filters-panel mb-2">
        <div class="admin-metricas-filters-row">
          <div class="admin-metricas-filter-cell">
            <label class="form-label fw-semibold small text-uppercase mb-1">Rango</label>
            <select v-model="filtros.rango" class="form-select admin-control">
              <option v-for="option in RANGO_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </div>
          <div class="admin-metricas-filter-cell">
            <label class="form-label fw-semibold small text-uppercase mb-1">Agrupacion</label>
            <select v-model="filtros.group_by" class="form-select admin-control">
              <option v-for="option in GROUP_BY_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </div>
          <div class="admin-metricas-filter-cell">
            <label class="form-label fw-semibold small text-uppercase mb-1">Top N</label>
            <input v-model.number="filtros.top_n" class="form-control admin-control" type="number" min="3" max="20" />
          </div>
          <div class="admin-metricas-filter-cell admin-metricas-filter-cell-wide">
            <button
              class="btn admin-metricas-btn-soft w-100"
              type="button"
              @click="mostrarSubfiltros = !mostrarSubfiltros"
            >
              {{ mostrarSubfiltros ? 'Ocultar subfiltros' : 'Mostrar subfiltros avanzados' }}
            </button>
          </div>

          <template v-if="filtros.rango === 'custom'">
            <div class="admin-metricas-filter-cell">
              <label class="form-label fw-semibold small text-uppercase mb-1">Fecha desde</label>
              <input v-model="filtros.fecha_desde" class="form-control admin-control" type="date" />
            </div>
            <div class="admin-metricas-filter-cell">
              <label class="form-label fw-semibold small text-uppercase mb-1">Fecha hasta</label>
              <input v-model="filtros.fecha_hasta" class="form-control admin-control" type="date" />
            </div>
          </template>
        </div>

        <div class="admin-metricas-estado-actions mt-2">
          <div class="admin-metricas-estado-switches">
            <p class="admin-metricas-group-title mb-0">Filtro principal por estado</p>
            <div class="admin-metricas-estado-chips">
              <button
                v-for="estado in ESTADO_OPTIONS"
                :key="estado.value"
                type="button"
                class="admin-metricas-chip"
                :class="{ 'admin-metricas-chip-active': filtros.estados[estado.value] }"
                @click="toggleEstado(estado.value)"
              >
                {{ estado.label }}
              </button>
            </div>
          </div>

          <div class="admin-metricas-actions-inline">
            <button class="btn admin-metricas-btn-ghost" type="button" :disabled="cargando" @click="limpiarFiltros">
              Limpiar filtros
            </button>
            <button class="btn admin-metricas-btn-primary" type="button" :disabled="cargando" @click="aplicarFiltros">
              {{ cargando ? 'Procesando...' : 'Aplicar analitica' }}
            </button>
          </div>
        </div>

        <Transition name="admin-expand">
          <div v-if="mostrarSubfiltros" class="admin-metricas-subfilters mt-2">
            <article class="admin-metricas-subfilter-card">
              <h3 class="h6 fw-bold mb-2">Subfiltro de segmentacion comercial</h3>
              <div class="row g-2">
                <div class="col-12">
                  <label class="form-label fw-semibold small text-uppercase mb-1">Paises (manual CSV)</label>
                  <input
                    v-model.trim="filtros.paises_manual"
                    class="form-control admin-control"
                    type="text"
                    placeholder="Ej: colombia, mexico, argentina"
                  />
                </div>
                <div class="col-12">
                  <p class="admin-metricas-subtitle mb-1">Sugeridos por datos actuales</p>
                  <div class="admin-metricas-chip-wrap">
                    <button
                      v-for="pais in sugerenciasPaises"
                      :key="pais"
                      type="button"
                      class="admin-metricas-chip admin-metricas-chip-soft"
                      :class="{ 'admin-metricas-chip-active': isPaisSeleccionado(pais) }"
                      @click="togglePaisSugerido(pais)"
                    >
                      {{ pais }}
                    </button>
                    <span v-if="!sugerenciasPaises.length" class="text-muted small">Aun no hay sugerencias de paises para este rango.</span>
                  </div>
                </div>
                <div class="col-12 col-lg-6">
                  <label class="form-label fw-semibold small text-uppercase mb-1">Monto minimo</label>
                  <input v-model.trim="filtros.min_total" class="form-control admin-control" type="number" min="0" step="0.01" />
                </div>
                <div class="col-12 col-lg-6">
                  <label class="form-label fw-semibold small text-uppercase mb-1">Monto maximo</label>
                  <input v-model.trim="filtros.max_total" class="form-control admin-control" type="number" min="0" step="0.01" />
                </div>
              </div>
            </article>

            <article class="admin-metricas-subfilter-card">
              <h3 class="h6 fw-bold mb-2">Subfiltro de catalogo y ranking</h3>
              <div class="row g-2">
                <div class="col-12 col-lg-6">
                  <label class="form-label fw-semibold small text-uppercase mb-1">Producto IDs (CSV)</label>
                  <input
                    v-model.trim="filtros.producto_ids"
                    class="form-control admin-control"
                    type="text"
                    placeholder="Ej: 7, 11, 15"
                  />
                </div>
                <div class="col-12 col-lg-6">
                  <label class="form-label fw-semibold small text-uppercase mb-1">Categoria IDs (CSV)</label>
                  <input
                    v-model.trim="filtros.categoria_ids"
                    class="form-control admin-control"
                    type="text"
                    placeholder="Ej: 80, 81"
                  />
                </div>
                <div class="col-12">
                  <div class="form-check form-switch mt-1">
                    <input
                      id="ventas-solo-aprobadas"
                      v-model="filtros.ventas_solo_aprobadas"
                      class="form-check-input"
                      type="checkbox"
                    />
                    <label class="form-check-label fw-semibold" for="ventas-solo-aprobadas">
                      Solo ventas aprobadas en rankings (recomendado)
                    </label>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </Transition>

      </section>

      <div v-if="error" class="alert alert-warning" role="alert">
        <p class="mb-0">{{ error }}</p>
      </div>

      <section class="admin-metricas-context-bar mb-2">
        <span v-for="item in filtroContextoItems" :key="item" class="admin-metricas-context-chip">{{ item }}</span>
      </section>

      <div v-if="cargando" class="admin-loading-box">
        <AppLoader variant="skeleton-cards" :count="4" />
      </div>

      <div v-else-if="!hasLoaded" class="empty-state-admin admin-metricas-empty">
        <p class="mb-2">Esta seccion usa carga bajo demanda para proteger la API.</p>
        <button class="btn btn-primary btn-sm" type="button" @click="cargarMetricas({ force: false })">
          Cargar primer analisis
        </button>
      </div>

      <template v-else-if="resumen">
        <section class="admin-metricas-kpi-grid mb-2">
          <article
            v-for="card in kpiCards"
            :key="card.key"
            class="admin-metricas-kpi-card"
            :class="`admin-metricas-kpi-card-${card.tone}`"
          >
            <p class="admin-metric-label mb-1">{{ card.label }}</p>
            <p class="admin-metricas-kpi-value mb-1">{{ card.value }}</p>
            <p class="admin-metricas-kpi-caption mb-0">{{ card.caption }}</p>
          </article>
        </section>

        <section class="admin-metricas-visual-grid mb-2">
          <article class="admin-card admin-metricas-chart-card">
            <div class="admin-card-header">
              <div>
                <p class="admin-metricas-card-kicker mb-1">Circulo de datos</p>
                <h3 class="h6 fw-bold mb-0">Distribucion monetaria</h3>
              </div>
              <small class="text-muted">Actualizado: {{ ultimaActualizacion }}</small>
            </div>
            <div class="admin-card-body admin-metricas-donut-wrap">
              <div class="admin-metricas-donut" :style="donutStyle">
                <div class="admin-metricas-donut-core">
                  <p class="mb-0 small text-uppercase text-muted">Total</p>
                  <p class="fw-bold mb-0">{{ formatMoney(donutSlices.total) }}</p>
                </div>
              </div>
              <div class="admin-metricas-legend">
                <article v-for="item in donutLegend" :key="item.label" class="admin-metricas-legend-item">
                  <span class="admin-metricas-legend-dot" :style="{ backgroundColor: item.color }" />
                  <div>
                    <p class="mb-0 fw-semibold">{{ item.label }}</p>
                    <p class="mb-0 text-muted small">{{ formatMoney(item.amount) }} · {{ formatPercent(item.share) }}</p>
                  </div>
                </article>
              </div>
            </div>
          </article>

          <article class="admin-card admin-metricas-chart-card">
            <div class="admin-card-header">
              <div>
                <p class="admin-metricas-card-kicker mb-1">Tendencia de ventas</p>
                <h3 class="h6 fw-bold mb-0">Monto generado por periodo</h3>
              </div>
              <small class="text-muted">Puntos: {{ tendenciaVisible.length }}</small>
            </div>
            <div class="admin-card-body">
              <div v-if="!tendenciaVisible.length" class="empty-state-admin">
                <p class="mb-0">No hay datos para construir la tendencia con los filtros actuales.</p>
              </div>
              <div v-else class="admin-metricas-trend-bars">
                <article v-for="item in tendenciaVisible" :key="item.periodo" class="admin-metricas-trend-item">
                  <div class="admin-metricas-trend-track">
                    <div
                      class="admin-metricas-trend-fill"
                      :style="{ height: `${(toNumber(item.total_generado) / tendenciaMax) * 100}%` }"
                    />
                  </div>
                  <p class="admin-metricas-trend-label mb-0">{{ item.periodo }}</p>
                  <p class="admin-metricas-trend-value mb-0">{{ formatMoney(item.total_generado) }}</p>
                </article>
              </div>
            </div>
          </article>
        </section>

        <section class="admin-metricas-visual-grid mb-2">
          <article class="admin-card">
            <div class="admin-card-header">
              <div>
                <p class="admin-metricas-card-kicker mb-1">Popularidad de productos</p>
                <h3 class="h6 fw-bold mb-0">Top productos por unidades vendidas</h3>
              </div>
            </div>
            <div class="admin-card-body">
              <div v-if="!topProductos.length" class="empty-state-admin">
                <p class="mb-0">No hay productos para mostrar en este rango.</p>
              </div>
              <div v-else class="admin-metricas-ranked-list">
                <article v-for="item in topProductos" :key="item.producto_id" class="admin-metricas-ranked-item">
                  <div class="d-flex justify-content-between align-items-start gap-2">
                    <div>
                      <p class="mb-0 fw-semibold text-truncate">{{ item.producto_nombre }}</p>
                      <p class="mb-0 small text-muted">{{ item.unidades }} unidades · {{ formatMoney(item.ingresos) }}</p>
                    </div>
                    <span class="admin-metricas-pill">{{ formatPercent(item.participacion_unidades) }}</span>
                  </div>
                  <div class="admin-metricas-progress-track">
                    <div
                      class="admin-metricas-progress-fill"
                      :style="{ width: `${(toNumber(item.unidades) / topProductosMaxUnidades) * 100}%` }"
                    />
                  </div>
                </article>
              </div>
            </div>
          </article>

          <article class="admin-card">
            <div class="admin-card-header">
              <div>
                <p class="admin-metricas-card-kicker mb-1">Categoria ganadora</p>
                <h3 class="h6 fw-bold mb-0">Top categorias por ingresos</h3>
              </div>
            </div>
            <div class="admin-card-body">
              <div v-if="!topCategorias.length" class="empty-state-admin">
                <p class="mb-0">No hay categorias para mostrar en este rango.</p>
              </div>
              <div v-else class="admin-metricas-ranked-list">
                <article v-for="item in topCategorias" :key="item.categoria_id" class="admin-metricas-ranked-item">
                  <div class="d-flex justify-content-between align-items-start gap-2">
                    <div>
                      <p class="mb-0 fw-semibold text-truncate">{{ item.categoria_nombre }}</p>
                      <p class="mb-0 small text-muted">{{ item.producto_nombre }} · {{ item.unidades }} unidades</p>
                    </div>
                    <span class="admin-metricas-pill">{{ formatMoney(item.ingresos) }}</span>
                  </div>
                  <div class="admin-metricas-progress-track">
                    <div
                      class="admin-metricas-progress-fill admin-metricas-progress-fill-secondary"
                      :style="{ width: `${(toNumber(item.ingresos) / topCategoriasMaxIngresos) * 100}%` }"
                    />
                  </div>
                </article>
              </div>
            </div>
          </article>
        </section>

        <section class="admin-metricas-table-grid mb-2">
          <article class="admin-card">
            <div class="admin-card-header">
              <div>
                <p class="admin-metricas-card-kicker mb-1">Mercados activos</p>
                <h3 class="h6 fw-bold mb-0">Paises con mayor demanda</h3>
              </div>
            </div>
            <div class="table-responsive">
              <table class="table table-sm align-middle mb-0 admin-metricas-table">
                <thead>
                  <tr>
                    <th scope="col">Pais</th>
                    <th scope="col" class="text-end">Pedidos</th>
                    <th scope="col" class="text-end">Participacion</th>
                    <th scope="col" class="text-end">Monto</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pais in topPaises" :key="pais.pais">
                    <td>{{ pais.pais }}</td>
                    <td class="text-end">{{ pais.cantidad_pedidos }}</td>
                    <td class="text-end">{{ formatPercent(pais.participacion_pedidos) }}</td>
                    <td class="text-end">{{ formatMoney(pais.monto_total) }}</td>
                  </tr>
                  <tr v-if="!topPaises.length">
                    <td colspan="4" class="text-center text-muted py-3">No hay paises con datos para el filtro actual.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>

          <article class="admin-card">
            <div class="admin-card-header">
              <div>
                <p class="admin-metricas-card-kicker mb-1">Estado de pipeline</p>
                <h3 class="h6 fw-bold mb-0">Distribucion por estado de pedido</h3>
              </div>
            </div>
            <div class="table-responsive">
              <table class="table table-sm align-middle mb-0 admin-metricas-table">
                <thead>
                  <tr>
                    <th scope="col">Estado</th>
                    <th scope="col" class="text-end">Pedidos</th>
                    <th scope="col" class="text-end">% Pedidos</th>
                    <th scope="col" class="text-end">Monto</th>
                    <th scope="col" class="text-end">% Monto</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="estado in estadoBreakdown" :key="estado.estado">
                    <td>{{ estado.etiqueta }}</td>
                    <td class="text-end">{{ estado.cantidad_pedidos }}</td>
                    <td class="text-end">{{ formatPercent(estado.participacion_pedidos) }}</td>
                    <td class="text-end">{{ formatMoney(estado.monto_total) }}</td>
                    <td class="text-end">{{ formatPercent(estado.participacion_monto) }}</td>
                  </tr>
                  <tr v-if="!estadoBreakdown.length">
                    <td colspan="5" class="text-center text-muted py-3">No hay estados disponibles para este filtro.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>

        <div class="admin-metricas-footnote">
          <span>
            Cache backend: {{ performanceInfo?.cached ? 'hit' : 'miss' }} · TTL {{ performanceInfo?.cache_ttl_seconds || '-' }}s
          </span>
          <span>
            Visitas: {{ visitantes?.disponible ? 'ok' : 'no disponible' }} · fuente {{ visitantes?.fuente || '-' }}
          </span>
          <span>Refrescado en: {{ ultimaActualizacion }}</span>
        </div>
      </template>

      <div v-else class="empty-state-admin">
        <p class="mb-0">No hay metricas disponibles todavia. Ajusta filtros y vuelve a consultar.</p>
      </div>
    </div>
  </InternalPanelLayout>
</template>
