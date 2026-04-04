<script setup>
import { computed, onMounted, ref } from 'vue'
import HeroBanner from '../components/common/HeroBanner.vue'
import AppLoader from '../components/common/AppLoader.vue'
import TicketCard from '../components/common/TicketCard.vue'
import { UI_TEXTS } from '../config/constants'
import { useCatalogStore } from '../stores/catalog'

const catalogStore = useCatalogStore()
const filtroEstadio = ref('')
const filtroUbicacion = ref('')
const filtroFecha = ref('')

onMounted(() => {
  catalogStore.loadProducts()
})

function normalizarTexto(valor) {
  return String(valor || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function obtenerUbicacionTicket(ticket) {
  return String(ticket?.ubicacion_estadio || ticket?.ubicacion || '').trim()
}

function formatearFechaLarga(valor) {
  if (!valor) return ''
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return ''
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
  }).format(fecha)
}

function formatearPrecio(valor, moneda = 'USD') {
  const numero = Number(valor)
  if (!Number.isFinite(numero) || numero <= 0) return 'Por definir'
  return `${numero.toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${String(moneda || 'USD').trim().toUpperCase()}`
}

function limpiarFiltros() {
  filtroEstadio.value = ''
  filtroUbicacion.value = ''
  filtroFecha.value = ''
}

function getTicketMetrics(ticket) {
  const categorias = Array.isArray(ticket?.categorias) ? ticket.categorias : []
  const categoriasActivas = categorias.filter((categoria) => categoria?.is_active !== false && categoria?.activo !== false)
  const unidades = categoriasActivas.reduce((acc, categoria) => {
    const disponibles = Number(categoria?.unidades_disponibles || 0)
    return acc + (Number.isFinite(disponibles) && disponibles > 0 ? disponibles : 0)
  }, 0)

  return {
    categorias: categoriasActivas.length,
    unidades,
  }
}

const estadiosDisponibles = computed(() => {
  const valores = new Map()
  for (const ticket of catalogStore.products) {
    const estadio = String(ticket?.estadio || '').trim()
    if (!estadio) continue
    const key = normalizarTexto(estadio)
    if (!valores.has(key)) valores.set(key, estadio)
  }

  return [...valores.values()].sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }))
})

const ubicacionesDisponibles = computed(() => {
  const valores = new Map()
  for (const ticket of catalogStore.products) {
    const ubicacion = obtenerUbicacionTicket(ticket)
    if (!ubicacion) continue
    const key = normalizarTexto(ubicacion)
    if (!valores.has(key)) valores.set(key, ubicacion)
  }

  return [...valores.values()].sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }))
})

const filtrosActivos = computed(() =>
  Boolean(filtroEstadio.value || filtroUbicacion.value || filtroFecha.value),
)

const ticketsFiltrados = computed(() => {
  const estadioSeleccionado = normalizarTexto(filtroEstadio.value)
  const ubicacionSeleccionada = normalizarTexto(filtroUbicacion.value)
  const fechaSeleccionada = filtroFecha.value ? new Date(`${filtroFecha.value}T00:00:00`) : null
  const fechaValida = fechaSeleccionada && !Number.isNaN(fechaSeleccionada.getTime()) ? fechaSeleccionada : null

  return catalogStore.products.filter((ticket) => {
    if (estadioSeleccionado && normalizarTexto(ticket?.estadio) !== estadioSeleccionado) {
      return false
    }

    if (ubicacionSeleccionada && normalizarTexto(obtenerUbicacionTicket(ticket)) !== ubicacionSeleccionada) {
      return false
    }

    if (fechaValida) {
      const fechaTicket = new Date(ticket?.fecha || '')
      if (Number.isNaN(fechaTicket.getTime()) || fechaTicket < fechaValida) {
        return false
      }
    }

    return true
  })
})

const rankedTickets = computed(() => {
  return [...ticketsFiltrados.value]
    .map((ticket) => ({
      ticket,
      metrics: getTicketMetrics(ticket),
    }))
    .sort((left, right) => {
      if (right.metrics.unidades !== left.metrics.unidades) {
        return right.metrics.unidades - left.metrics.unidades
      }
      if (right.metrics.categorias !== left.metrics.categorias) {
        return right.metrics.categorias - left.metrics.categorias
      }
      return Number(right.ticket?.id || 0) - Number(left.ticket?.id || 0)
    })
})

const rankedPopularTickets = computed(() => {
  return [...catalogStore.products]
    .map((ticket) => ({
      ticket,
      metrics: getTicketMetrics(ticket),
    }))
    .sort((left, right) => {
      if (right.metrics.unidades !== left.metrics.unidades) {
        return right.metrics.unidades - left.metrics.unidades
      }
      if (right.metrics.categorias !== left.metrics.categorias) {
        return right.metrics.categorias - left.metrics.categorias
      }
      return Number(right.ticket?.id || 0) - Number(left.ticket?.id || 0)
    })
})

const popularTickets = computed(() => rankedPopularTickets.value.slice(0, 3).map((item) => item.ticket))

const headerStats = computed(() => {
  const totals = catalogStore.products.reduce(
    (acc, ticket) => {
      const metrics = getTicketMetrics(ticket)
      acc.categorias += metrics.categorias
      acc.unidades += metrics.unidades
      return acc
    },
    { categorias: 0, unidades: 0 },
  )

  return {
    tickets: catalogStore.products.length,
    categorias: totals.categorias,
    unidades: totals.unidades,
  }
})

const resumenFiltrado = computed(() =>
  rankedTickets.value.reduce(
    (acc, item) => {
      acc.categorias += item.metrics.categorias
      acc.unidades += item.metrics.unidades
      return acc
    },
    { categorias: 0, unidades: 0 },
  ),
)

const fechaMasProximaFiltrada = computed(() => {
  const fechas = ticketsFiltrados.value
    .map((ticket) => new Date(ticket?.fecha || ''))
    .filter((fecha) => !Number.isNaN(fecha.getTime()))
    .sort((a, b) => a.getTime() - b.getTime())

  if (!fechas.length) return ''
  return formatearFechaLarga(fechas[0])
})

const rangoFechasFiltrado = computed(() => {
  const fechas = ticketsFiltrados.value
    .map((ticket) => new Date(ticket?.fecha || ''))
    .filter((fecha) => !Number.isNaN(fecha.getTime()))
    .sort((a, b) => a.getTime() - b.getTime())

  if (!fechas.length) return 'Fechas sujetas a publicación por ticket.'

  const inicio = formatearFechaLarga(fechas[0])
  const fin = formatearFechaLarga(fechas[fechas.length - 1])
  if (inicio === fin) return `Partidos disponibles para ${inicio}.`
  return `Partidos visibles entre ${inicio} y ${fin}.`
})

const resumenSedesFiltrado = computed(() => {
  const estadios = new Set()
  const ubicaciones = new Set()

  for (const ticket of ticketsFiltrados.value) {
    const estadio = String(ticket?.estadio || '').trim()
    const ubicacion = obtenerUbicacionTicket(ticket)
    if (estadio) estadios.add(normalizarTexto(estadio))
    if (ubicacion) ubicaciones.add(normalizarTexto(ubicacion))
  }

  return {
    estadios: estadios.size,
    ubicaciones: ubicaciones.size,
  }
})

const rangoPrecioFiltrado = computed(() => {
  const precios = []
  let monedaPrincipal = 'USD'

  for (const ticket of ticketsFiltrados.value) {
    const categorias = Array.isArray(ticket?.categorias) ? ticket.categorias : []
    for (const categoria of categorias) {
      if (categoria?.is_active === false || categoria?.activo === false) continue
      const precio = Number(categoria?.precio)
      if (Number.isFinite(precio) && precio > 0) {
        precios.push(precio)
        if (categoria?.moneda && monedaPrincipal === 'USD') {
          monedaPrincipal = categoria.moneda
        }
      }
    }
  }

  if (!precios.length) return 'Precio según categoría disponible.'

  const minimo = Math.min(...precios)
  const maximo = Math.max(...precios)
  if (minimo === maximo) return `Precio estimado: ${formatearPrecio(minimo, monedaPrincipal)}.`
  return `Rango estimado: ${formatearPrecio(minimo, monedaPrincipal)} - ${formatearPrecio(maximo, monedaPrincipal)}.`
})

const tituloContextoCatalogo = computed(() => {
  if (!ticketsFiltrados.value.length) return 'Guía para encontrar tus boletos ideales en el Mundial 2026'
  if (filtrosActivos.value) return 'Guía completa para comparar las opciones que ya filtraste'
  return 'Todo lo que necesitas para elegir boletos con confianza'
})

const descripcionContextoCatalogo = computed(() => {
  if (!ticketsFiltrados.value.length) {
    return 'Con los filtros actuales no hay resultados. Prueba otra combinación de estadio, ubicación o fecha y volverás a ver más partidos para comparar.'
  }

  return `${rangoFechasFiltrado.value} ${rangoPrecioFiltrado.value} Esta guía te ayuda a entender rápido cómo comparar, cuándo comprar y qué revisar antes de pagar.`
})

const badgesContextoCatalogo = computed(() => {
  const badges = [
    `${ticketsFiltrados.value.length} tickets visibles`,
    `${resumenFiltrado.value.categorias} categorías reportadas`,
    `${resumenFiltrado.value.unidades} entradas disponibles`,
    `${resumenSedesFiltrado.value.estadios} estadios`,
    `${resumenSedesFiltrado.value.ubicaciones} ubicaciones`,
  ]

  if (fechaMasProximaFiltrada.value) {
    badges.push(`Próxima fecha: ${fechaMasProximaFiltrada.value}`)
  }

  return badges
})

const introduccionContextoCatalogo = computed(() => {
  const base = [
    'El Mundial es uno de los eventos deportivos más seguidos del planeta: reúne aficiones de distintos países, idiomas y culturas en una sola competencia.',
    'La edición 2026 será histórica por su escala: más selecciones, más partidos y más sedes. Para los aficionados, eso se traduce en más opciones para vivir el torneo en vivo.',
    'En esta página puedes revisar boletos por sede, fecha y disponibilidad en un solo lugar, sin tener que navegar entre múltiples páginas para entender qué te conviene.',
  ]

  if (filtrosActivos.value) {
    base.push(`Con tus filtros activos estás revisando ${ticketsFiltrados.value.length} opciones enfocadas en tu plan actual.`)
  } else {
    base.push('Si todavía no tienes un partido definido, puedes empezar comparando ciudad, estadio y etapa para encontrar el mejor equilibrio entre experiencia y presupuesto.')
  }

  return base
})

const factoresPrecioCatalogo = computed(() => [
  {
    titulo: 'Importancia del partido',
    descripcion:
      'No todos los encuentros se comportan igual: las fases de eliminación directa suelen concentrar mayor interés y tienden a tener precios más altos que la fase de grupos.',
  },
  {
    titulo: 'Selecciones que juegan',
    descripcion:
      'Partidos con equipos de alta demanda suelen moverse más rápido. Si tu prioridad es ver una selección específica, conviene monitorear su disponibilidad con frecuencia.',
  },
  {
    titulo: 'Sede y ciudad anfitriona',
    descripcion:
      'Algunas ciudades reciben más demanda por conectividad, capacidad del estadio o atractivo turístico. Eso puede influir directamente en los precios visibles.',
  },
  {
    titulo: 'Categoría de asiento',
    descripcion:
      'La ubicación en el estadio cambia la experiencia y el costo: zonas más cercanas al campo suelen tener precio superior frente a ubicaciones altas o de esquina.',
  },
  {
    titulo: 'Momento de compra',
    descripcion:
      'Los precios pueden variar a medida que se acerca la fecha del partido. En algunos casos suben por demanda y en otros bajan por ajustes de oferta.',
  },
  {
    titulo: 'Comportamiento del mercado',
    descripcion:
      `Las variaciones en inventario y demanda se reflejan en tiempo real. Hoy, en esta selección, el ${rangoPrecioFiltrado.value.toLowerCase()}`,
  },
])

const comparacionContextoCatalogo = computed(() => [
  'Compara primero por ciudad y estadio para priorizar logística, y luego por categoría para ajustar presupuesto.',
  'Usa la fecha como filtro cuando tengas ventanas de viaje definidas: te ahorra tiempo y evita revisar partidos fuera de tu plan.',
  'Antes de comprar, entra al detalle del ticket y revisa categorías activas, cupos disponibles y condiciones de compra por persona.',
  'Si estás entre dos opciones parecidas, prioriza la que combine mejor ubicación, disponibilidad y comodidad de acceso.',
  'Cuando veas una categoría con pocas entradas y precio adecuado, conviene decidir rápido para evitar cambios por demanda.',
])

const estrategiasAhorroCatalogo = computed(() => [
  'Evalúa partidos de fase de grupos: en muchos casos ofrecen mejor relación entre experiencia y presupuesto.',
  'Considera sedes alternas dentro de tu ruta de viaje; algunas ciudades pueden tener diferencias de precio relevantes.',
  'Sé flexible con la fecha cuando puedas: esa flexibilidad suele abrir opciones más competitivas.',
  'Haz seguimiento frecuente de los partidos que te interesan: el inventario puede cambiar durante el día.',
  'Evita comparar solo por precio final; también valora visibilidad de la zona, ambiente y facilidad de acceso al estadio.',
])

const categoriasReferenciaCatalogo = computed(() => [
  {
    categoria: 'Categoría 1',
    descripcion:
      'Generalmente corresponde a zonas premium con visual más directa del juego. Suele ser la opción de mayor precio.',
  },
  {
    categoria: 'Categoría 2',
    descripcion:
      'Ubicaciones con gran visibilidad y mejor balance para quienes quieren buena experiencia sin ir al máximo costo.',
  },
  {
    categoria: 'Categoría 3',
    descripcion:
      'Alternativa intermedia que mantiene buena experiencia de partido con un presupuesto más contenido.',
  },
  {
    categoria: 'Categoría 4',
    descripcion:
      'Suele ser la entrada más accesible para vivir el evento en el estadio. Disponibilidad y condiciones varían por sede.',
  },
])

const calendarioRondasCatalogo = computed(() => [
  {
    etapa: 'Fase de grupos',
    fechas: '11 jun - 27 jun',
    detalle: 'Inicio del torneo con mayor volumen de partidos y múltiples opciones por sede.',
  },
  {
    etapa: 'Dieciseisavos (Round of 32)',
    fechas: '28 jun - 3 jul',
    detalle: 'Primera ronda de eliminación directa en el nuevo formato ampliado.',
  },
  {
    etapa: 'Octavos de final',
    fechas: '4 jul - 7 jul',
    detalle: 'Cruces de alta tensión donde la demanda suele incrementarse.',
  },
  {
    etapa: 'Cuartos de final',
    fechas: '9 jul - 11 jul',
    detalle: 'Partidos decisivos con menos encuentros disponibles y mayor atención global.',
  },
  {
    etapa: 'Semifinales',
    fechas: '14 jul - 15 jul',
    detalle: 'Dos encuentros clave que definen la final y el partido por el tercer lugar.',
  },
  {
    etapa: 'Final',
    fechas: '19 jul',
    detalle: 'Cierre del torneo con la disputa por el título mundial.',
  },
])

const formatoTorneoCatalogo = computed(() => [
  {
    etapa: '48 selecciones en competencia',
    descripcion:
      'El torneo crece en participación y representación global, con más países y más historias deportivas por seguir.',
  },
  {
    etapa: '12 grupos iniciales',
    descripcion:
      'Cada selección juega tres partidos en fase de grupos para definir su continuidad en la competencia.',
  },
  {
    etapa: 'Clasificación a eliminación directa',
    descripcion:
      'Avanzan los mejores equipos y desde ahí cada partido define continuidad o eliminación.',
  },
  {
    etapa: 'Tramo final de alta demanda',
    descripcion:
      'Cuartos, semifinales y final concentran alta atención; por eso conviene anticipar seguimiento y decisión.',
  },
])

const preguntasContextoCatalogo = computed(() => [
  {
    pregunta: '¿Cómo sé si aún hay disponibilidad real?',
    respuesta:
      'La disponibilidad se actualiza en la plataforma según el inventario activo de cada categoría al momento de consultar.',
  },
  {
    pregunta: '¿Qué hago si no encuentro el partido que busco de inmediato?',
    respuesta:
      'Ajusta filtros de estadio, ubicación o fecha para ampliar resultados y vuelve a revisar opciones en el catálogo.',
  },
  {
    pregunta: '¿Cuándo conviene comprar?',
    respuesta:
      'Cuando encuentres categoría con precio y cupos adecuados para tu plan. La demanda puede modificar disponibilidad durante el día.',
  },
  {
    pregunta: '¿Cómo comparar dos partidos parecidos?',
    respuesta:
      'Compara primero logística (ciudad, estadio y fecha), luego categoría de asiento y finalmente disponibilidad activa para decidir con más claridad.',
  },
  {
    pregunta: '¿Las categorías son iguales en todos los estadios?',
    respuesta:
      'La lógica de categorías es similar, pero la distribución de zonas cambia por estadio. Por eso conviene revisar el detalle específico de cada ticket.',
  },
  {
    pregunta: '¿Puedo empezar por presupuesto y luego elegir partido?',
    respuesta:
      'Sí. Es una estrategia práctica: filtra por sede/fecha, revisa rangos por categoría y elige el partido que mejor encaje en tu presupuesto.',
  },
])

const notaContextoCatalogo = computed(
  () =>
    'Nota: fechas, precios y disponibilidad pueden cambiar por dinámica de inventario y demanda. Revisa siempre el detalle actualizado antes de confirmar tu compra.',
)

function formatMatchesCount(ticket) {
  const metrics = getTicketMetrics(ticket)
  const etiquetaCategorias = `${metrics.categorias} ${metrics.categorias === 1 ? 'categoría' : 'categorías'}`
  return `${etiquetaCategorias} · ${metrics.unidades} disponibles`
}
</script>

<template>
  <div class="home-shell">
    <section class="home-dark-zone pb-4">
      <HeroBanner :stats="headerStats" :is-loading="catalogStore.isLoadingProducts" />

      <section class="container pt-1 home-popular-block">
        <div class="d-flex align-items-center mb-3">
          <h2 class="section-title-light mb-0">Popular tickets</h2>
        </div>

        <AppLoader v-if="catalogStore.isLoadingProducts" variant="skeleton-home" :count="4" />

        <div v-else-if="catalogStore.productsError" class="alert alert-warning border-0 py-2 px-3 mb-3" role="alert">
          {{ catalogStore.productsError }}
        </div>

        <div v-else-if="popularTickets.length" class="row g-3">
          <div v-for="(ticket, index) in popularTickets" :key="ticket.id" class="col-12 col-lg-4">
            <RouterLink
              class="popular-ticket"
              :style="{ '--stagger-index': index }"
              :to="`/tickets/${ticket.id}/categorias`"
            >
              <img
                v-if="ticket.imagen"
                class="popular-ticket-thumb"
                :src="ticket.imagen"
                :alt="`Imagen de ${ticket.nombre}`"
                loading="lazy"
              />
              <div v-else class="popular-ticket-thumb-fallback" aria-hidden="true"></div>
              <div>
                <h3 class="popular-ticket-title mb-1">{{ ticket.nombre }}</h3>
                <p class="popular-ticket-meta mb-0">{{ formatMatchesCount(ticket) }}</p>
              </div>
              <span class="popular-ticket-arrow">›</span>
            </RouterLink>
          </div>
        </div>

        <div v-else class="small text-white-50 py-2">
          No hay tickets destacados por el momento.
        </div>
      </section>
    </section>

    <section class="home-filters-stage">
      <div class="container home-filters-wrap">
        <article class="home-filters-panel" aria-label="Filtros de tickets">
          <div class="home-filters-head">
            <div>
              <p class="home-filters-kicker mb-1">Filtrar tickets</p>
              <h2 class="home-filters-title mb-1">Encuentra más rápido el ticket ideal</h2>
              <p class="home-filters-subtitle mb-0">Filtra por estadio, ubicación y fecha.</p>
            </div>

            <button
              type="button"
              class="btn btn-outline-light btn-sm"
              :disabled="!filtrosActivos"
              @click="limpiarFiltros"
            >
              Limpiar filtros
            </button>
          </div>

          <div class="home-filters-grid" role="group" aria-label="Controles de filtrado">
            <label class="home-filter-field">
              <span class="home-filter-label">Estadio</span>
              <select v-model="filtroEstadio" class="form-select home-filter-control">
                <option value="">Todos</option>
                <option v-for="estadio in estadiosDisponibles" :key="estadio" :value="estadio">
                  {{ estadio }}
                </option>
              </select>
            </label>

            <label class="home-filter-field">
              <span class="home-filter-label">Ubicación</span>
              <select v-model="filtroUbicacion" class="form-select home-filter-control">
                <option value="">Todas</option>
                <option v-for="ubicacion in ubicacionesDisponibles" :key="ubicacion" :value="ubicacion">
                  {{ ubicacion }}
                </option>
              </select>
            </label>

            <label class="home-filter-field">
              <span class="home-filter-label">Desde fecha</span>
              <input v-model="filtroFecha" type="date" class="form-control home-filter-control" />
            </label>
          </div>

          <p class="home-filters-summary mb-0">
            Mostrando <strong>{{ ticketsFiltrados.length }}</strong> de {{ catalogStore.products.length }} tickets.
          </p>
        </article>
      </div>
    </section>

    <section class="home-stage-zone">
      <div class="container stage-inner py-4 py-lg-5">
        <div class="d-flex flex-column flex-lg-row align-items-lg-end justify-content-between gap-3 mb-4">
          <div>
            <p class="text-uppercase small fw-semibold text-secondary mb-2">Boletos disponibles</p>
            <h2 class="h3 fw-bold mb-1">Elige tu partido y entra al detalle de categorías</h2>
            <p class="text-muted mb-0">Información clara de sede, fecha y disponibilidad en una sola lectura.</p>
          </div>
          <span class="text-muted fw-semibold">
            {{ filtrosActivos ? `Mostrando ${ticketsFiltrados.length} de ${catalogStore.products.length} tickets` : 'Inventario actualizado constantemente' }}
          </span>
        </div>

        <AppLoader v-if="catalogStore.isLoadingProducts" variant="skeleton-cards" :count="8" />

        <div v-else-if="catalogStore.productsError" class="alert alert-warning border mt-3" role="alert">
          {{ catalogStore.productsError }}
        </div>

        <div v-else-if="ticketsFiltrados.length" class="row g-4">
          <div
            v-for="(ticket, index) in ticketsFiltrados"
            :key="ticket.id"
            class="col-12 col-md-6 col-xl-3"
            :style="{ '--stagger-index': index }"
          >
            <TicketCard :ticket="ticket" />
          </div>
        </div>

        <div
          v-else-if="catalogStore.products.length"
          class="alert alert-light border mt-3 d-flex flex-column flex-lg-row align-items-start align-items-lg-center justify-content-between gap-3"
          role="alert"
        >
          <span>No encontramos tickets con los filtros actuales. Ajusta tus criterios para ver más opciones.</span>
          <button type="button" class="btn btn-outline-primary btn-sm" @click="limpiarFiltros">
            Restablecer filtros
          </button>
        </div>

        <div v-else class="alert alert-light border mt-3" role="alert">
          {{ UI_TEXTS.catalog.empty }}
        </div>

        <section
          v-if="!catalogStore.isLoadingProducts && !catalogStore.productsError && catalogStore.products.length"
          class="home-catalog-context mt-4 mt-lg-5"
          aria-label="Contexto adicional del catálogo"
        >
          <div class="home-catalog-context-intro">
            <p class="home-catalog-context-kicker mb-1">Guía de compra</p>
            <h3 class="home-catalog-context-title mb-2">{{ tituloContextoCatalogo }}</h3>
            <p class="home-catalog-context-text mb-3">{{ descripcionContextoCatalogo }}</p>

            <div class="home-catalog-context-badges" role="list" aria-label="Resumen de contexto">
              <span
                v-for="badge in badgesContextoCatalogo"
                :key="badge"
                class="home-catalog-context-badge"
                role="listitem"
              >
                {{ badge }}
              </span>
            </div>
          </div>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">2026 FIFA World Cup tickets: contexto clave</h4>
            <div class="home-catalog-context-paragraphs">
              <p
                v-for="parrafo in introduccionContextoCatalogo"
                :key="parrafo"
                class="home-catalog-context-paragraph mb-0"
              >
                {{ parrafo }}
              </p>
            </div>
          </section>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">¿Qué influye en el precio de los boletos?</h4>
            <div class="home-catalog-context-grid home-catalog-context-grid-factors">
              <article
                v-for="factor in factoresPrecioCatalogo"
                :key="factor.titulo"
                class="home-catalog-context-card"
              >
                <p class="home-catalog-context-item-title mb-1">{{ factor.titulo }}</p>
                <p class="home-catalog-context-item-text mb-0">{{ factor.descripcion }}</p>
              </article>
            </div>
          </section>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">Cómo comparar mejor tus opciones</h4>
            <ul class="home-catalog-context-list mb-0">
              <li v-for="tip in comparacionContextoCatalogo" :key="tip">{{ tip }}</li>
            </ul>
          </section>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">Estrategias para encontrar mejor precio</h4>
            <ul class="home-catalog-context-list mb-0">
              <li v-for="estrategia in estrategiasAhorroCatalogo" :key="estrategia">{{ estrategia }}</li>
            </ul>
          </section>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">Categorías de boletos: guía rápida</h4>
            <div class="home-catalog-context-category-grid">
              <article
                v-for="categoria in categoriasReferenciaCatalogo"
                :key="categoria.categoria"
                class="home-catalog-context-category-card"
              >
                <p class="home-catalog-context-category-label mb-1">{{ categoria.categoria }}</p>
                <p class="home-catalog-context-category-text mb-0">{{ categoria.descripcion }}</p>
              </article>
            </div>
          </section>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">Calendario general del torneo 2026</h4>
            <div class="home-catalog-context-timeline">
              <article
                v-for="ronda in calendarioRondasCatalogo"
                :key="ronda.etapa"
                class="home-catalog-context-timeline-card"
              >
                <p class="home-catalog-context-timeline-stage mb-1">{{ ronda.etapa }}</p>
                <p class="home-catalog-context-timeline-dates mb-1">{{ ronda.fechas }}</p>
                <p class="home-catalog-context-timeline-text mb-0">{{ ronda.detalle }}</p>
              </article>
            </div>
          </section>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">¿Cómo funciona el formato del Mundial 2026?</h4>
            <div class="home-catalog-context-grid home-catalog-context-grid-format">
              <article
                v-for="bloque in formatoTorneoCatalogo"
                :key="bloque.etapa"
                class="home-catalog-context-card"
              >
                <p class="home-catalog-context-item-title mb-1">{{ bloque.etapa }}</p>
                <p class="home-catalog-context-item-text mb-0">{{ bloque.descripcion }}</p>
              </article>
            </div>
          </section>

          <section class="home-catalog-context-section">
            <h4 class="home-catalog-context-section-title mb-2">Preguntas frecuentes para decidir más rápido</h4>
            <div class="home-catalog-context-faq-list">
              <article
                v-for="pregunta in preguntasContextoCatalogo"
                :key="pregunta.pregunta"
                class="home-catalog-context-faq-item"
              >
                <p class="home-catalog-context-faq-question mb-1">{{ pregunta.pregunta }}</p>
                <p class="home-catalog-context-faq-answer mb-0">{{ pregunta.respuesta }}</p>
              </article>
            </div>
          </section>

          <p class="home-catalog-context-note mb-0 mt-3">
            {{ notaContextoCatalogo }}
          </p>
        </section>
      </div>
    </section>
  </div>
</template>
