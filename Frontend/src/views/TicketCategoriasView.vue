<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppLoader from '../components/common/AppLoader.vue'
import { useCatalogStore } from '../stores/catalog'
import { useCarritoStore } from '../stores/carrito'
import { stagger, transicionModal } from '../utils/animations'

const route = useRoute()
const catalogStore = useCatalogStore()
const carritoStore = useCarritoStore()
const ticketId = computed(() => Number(route.params.ticketId))

const productoActual = computed(() =>
  catalogStore.products.find((item) => item.id === ticketId.value),
)

const fechaEvento = computed(() => {
  const fecha = productoActual.value?.fecha
  if (!fecha) return ''
  const date = new Date(fecha)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
})

const ciudadEvento = computed(() => productoActual.value?.ubicacion_estadio || productoActual.value?.ubicacion || '')

const estadioEvento = computed(() => productoActual.value?.estadio || '')

const bloqueFecha = computed(() => {
  const fecha = productoActual.value?.fecha
  if (!fecha) return null
  const date = new Date(fecha)
  if (Number.isNaN(date.getTime())) return null

  const diaNumero = new Intl.DateTimeFormat('es-CO', { day: '2-digit' }).format(date)
  const mesCorto = new Intl.DateTimeFormat('es-CO', { month: 'short' }).format(date).replace('.', '')
  const diaSemana = new Intl.DateTimeFormat('es-CO', { weekday: 'short' }).format(date).replace('.', '')

  return {
    diaNumero,
    mesCorto,
    diaSemana,
  }
})

const categoriasCrudas = computed(() => catalogStore.categoriesByProduct[ticketId.value] || [])
const errorCategorias = computed(() => catalogStore.categoriesErrorByProduct[ticketId.value] || '')

const formatearPrecio = (categoria) => {
  if (!categoria || categoria.precio == null) return ''
  const value = Number(categoria.precio)
  if (Number.isNaN(value)) return ''

  return `${value.toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${categoria.moneda || ''}`.trim()
}

const esCategoriaDisponible = (categoria) =>
  categoria?.activo !== false &&
  categoria?.is_active !== false &&
  Number(categoria?.unidades_disponibles) > 0

const unidadesDisponibles = (categoria) => Number(categoria?.unidades_disponibles) || 0

const esStockBajo = (categoria) => {
  const unidades = unidadesDisponibles(categoria)
  return unidades > 0 && unidades <= 5
}

const etiquetaDisponibilidad = (categoria) => {
  const unidades = unidadesDisponibles(categoria)
  if (!unidades) return 'Agotado'
  if (unidades === 1) return 'Queda 1'
  if (unidades <= 5) return `Quedan ${unidades}`
  return 'Disponible'
}

const textoUrgencia = (categoria) => {
  const unidades = unidadesDisponibles(categoria)
  if (unidades > 0 && unidades <= 5) {
    return unidades === 1 ? 'Sólo queda 1 entrada' : `Sólo quedan ${unidades} entradas`
  }
  return ''
}

const categoriasOrdenadas = computed(() => {
  const items = [...categoriasCrudas.value]
  items.sort((a, b) => {
    const ad = esCategoriaDisponible(a) ? 1 : 0
    const bd = esCategoriaDisponible(b) ? 1 : 0
    if (ad !== bd) return bd - ad
    return unidadesDisponibles(b) - unidadesDisponibles(a)
  })
  return items
})

const categoriasDisponibles = computed(() =>
  categoriasOrdenadas.value.filter((categoria) => esCategoriaDisponible(categoria)),
)

const totalUnidadesDisponibles = computed(() =>
  categoriasDisponibles.value.reduce((acc, categoria) => acc + unidadesDisponibles(categoria), 0),
)

const rangoPrecios = computed(() => {
  const precios = categoriasDisponibles.value
    .map((categoria) => Number(categoria?.precio))
    .filter((valor) => Number.isFinite(valor) && valor > 0)

  if (!precios.length) return null

  return {
    minimo: Math.min(...precios),
    maximo: Math.max(...precios),
  }
})

const limitePromedioPorPersona = computed(() => {
  const limites = categoriasDisponibles.value
    .map((categoria) => Number(categoria?.limite_por_usuario || 0))
    .filter((valor) => Number.isFinite(valor) && valor > 0)

  if (!limites.length) return null

  const promedio = limites.reduce((acc, valor) => acc + valor, 0) / limites.length
  return Math.max(1, Math.round(promedio))
})

const monedaPrincipal = computed(() => {
  const moneda = categoriasOrdenadas.value.find((categoria) => categoria?.moneda)?.moneda
  return String(moneda || 'USD').trim().toUpperCase() || 'USD'
})

const formatearMoneda = (valor) => {
  const numero = Number(valor)
  if (!Number.isFinite(numero) || numero <= 0) return 'Por definir'

  return `${numero.toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${monedaPrincipal.value}`
}

const precioDesdeTexto = computed(() => {
  if (!rangoPrecios.value) return 'Por definir'
  return formatearMoneda(rangoPrecios.value.minimo)
})

const precioRangoTexto = computed(() => {
  if (!rangoPrecios.value) return 'Por definir'
  if (rangoPrecios.value.minimo === rangoPrecios.value.maximo) {
    return formatearMoneda(rangoPrecios.value.minimo)
  }
  return `${formatearMoneda(rangoPrecios.value.minimo)} - ${formatearMoneda(rangoPrecios.value.maximo)}`
})

const tituloContexto = computed(() => {
  const nombre = String(productoActual.value?.nombre || '').trim()
  if (!nombre) return 'Encuentra la categoría perfecta para tu experiencia'
  return `Vive ${nombre} con la categoría que mejor se adapte a tu plan`
})

const descripcionContexto = computed(() => {
  const partes = []
  if (fechaEvento.value) partes.push(`Evento programado para ${fechaEvento.value}`)
  if (estadioEvento.value) partes.push(`en ${estadioEvento.value}`)
  if (ciudadEvento.value) partes.push(`(${ciudadEvento.value})`)

  const contextoEvento = partes.join(' ').trim()
  if (contextoEvento) {
    return `${contextoEvento}. Revisa precios, disponibilidad y límites por persona antes de elegir tu ubicación ideal.`
  }

  return 'Compara cada categoría por disponibilidad y precio para asegurar tu entrada en minutos con una decisión informada.'
})

const contextoBadges = computed(() => {
  const badges = [
    `${categoriasDisponibles.value.length} categorías activas ahora`,
    `${totalUnidadesDisponibles.value.toLocaleString('es-CO')} entradas reportadas`,
    `Precios desde ${precioDesdeTexto.value}`,
    'Checkout seguro y confirmación inmediata',
  ]

  if (ciudadEvento.value) {
    badges.unshift(`Sede: ${ciudadEvento.value}`)
  }

  return badges.slice(0, 5)
})

const contextoGuiaCompra = computed(() => {
  const limiteTexto = limitePromedioPorPersona.value
    ? `${limitePromedioPorPersona.value} boletos por persona`
    : 'un límite que varía por categoría'

  return [
    {
      titulo: 'Cómo elegir tu categoría',
      descripcion:
        'Compara ubicación, precio y disponibilidad para definir la opción que mejor encaja con tu experiencia ideal.',
    },
    {
      titulo: 'Qué puede mover el precio',
      descripcion: `Hoy el rango va de ${precioRangoTexto.value}. La demanda y el inventario disponible pueden modificar estos valores.`,
    },
    {
      titulo: 'Compra en grupo sin fricciones',
      descripcion: `Para compras múltiples, revisa ${limiteTexto} y asegúrate de completar tu selección en una sola operación.`,
    },
    {
      titulo: 'Compra segura y confirmación',
      descripcion:
        'Cuando completes tu pago, recibirás confirmación de pedido y seguimiento para que tengas claridad de cada paso.',
    },
  ]
})

const preguntasRapidas = computed(() => [
  {
    pregunta: '¿Por qué cambia la disponibilidad?',
    respuesta:
      'Porque la compra se realiza en tiempo real: cuando una categoría se vende, su inventario se actualiza de inmediato.',
  },
  {
    pregunta: '¿Cómo sé cuál categoría me conviene?',
    respuesta:
      'Empieza por tu presupuesto y luego compara ubicación y límite por persona para elegir la opción más cómoda para tu plan.',
  },
  {
    pregunta: '¿Cuándo es mejor comprar?',
    respuesta:
      'Si una categoría tiene pocas entradas o un precio que te funciona, conviene asegurarla pronto para evitar cambios por demanda.',
  },
])

const categoriaActiva = ref(null)
const modalAbierto = ref(false)

const cantidadesSeleccionadas = ref({})

const maximoPorCategoria = (categoria) => {
  const stock = unidadesDisponibles(categoria)
  const maxUser = categoria?.limite_por_usuario ? Number(categoria.limite_por_usuario) : null
  if (!stock) return 0
  if (maxUser && maxUser > 0) {
    return Math.min(stock, maxUser)
  }
  return stock
}

const cantidadParaCategoria = (categoria) => {
  const max = maximoPorCategoria(categoria)
  if (!max) return 0
  const current = Number(cantidadesSeleccionadas.value[categoria.id] ?? 1)
  if (Number.isNaN(current) || current < 1) return 1
  if (current > max) return max
  return current
}

const fijarCantidadParaCategoria = (categoria, value) => {
  const max = maximoPorCategoria(categoria)
  if (!max) {
    cantidadesSeleccionadas.value[categoria.id] = 0
    return
  }
  let next = Number(value)
  if (Number.isNaN(next) || next < 1) next = 1
  if (next > max) next = max
  cantidadesSeleccionadas.value[categoria.id] = next
}

const decrementarCantidad = (categoria) => {
  const current = cantidadParaCategoria(categoria)
  if (current <= 1) return
  fijarCantidadParaCategoria(categoria, current - 1)
}

const incrementarCantidad = (categoria) => {
  const current = cantidadParaCategoria(categoria)
  const max = maximoPorCategoria(categoria)
  if (!max || current >= max) return
  fijarCantidadParaCategoria(categoria, current + 1)
}

const abrirModalCategoria = (categoria) => {
  if (!categoria) return
  categoriaActiva.value = categoria
  if (!cantidadesSeleccionadas.value[categoria.id] && esCategoriaDisponible(categoria)) {
    cantidadesSeleccionadas.value[categoria.id] = 1
  }
  modalAbierto.value = true
}

const cerrarModal = () => {
  modalAbierto.value = false
  categoriaActiva.value = null
}

const agregarCategoriaAlCarrito = () => {
  const categoria = categoriaActiva.value
  if (!categoria || !esCategoriaDisponible(categoria)) return

  const cantidad = cantidadParaCategoria(categoria)
  if (cantidad <= 0) return

  carritoStore.agregarItem({
    idCategoria: categoria.id,
    idProducto: productoActual.value?.id || 0,
    nombreEvento: productoActual.value?.nombre || '',
    nombreCategoria: categoria.nombre,
    fechaEvento: productoActual.value?.fecha || '',
    maximoPermitido: maximoPorCategoria(categoria),
    precioUnitario: Number(categoria.precio || 0),
    cantidad,
  })

  cerrarModal()
}

onMounted(async () => {
  carritoStore.inicializar()
  if (!catalogStore.products.length) {
    await catalogStore.loadProducts()
  }
  await catalogStore.loadCategoriesForProduct(ticketId.value)
})
</script>

<template>
  <div class="categorias-vista">
    <section class="container pt-3 pt-lg-4 pb-3 pb-lg-4">
      <header class="categorias-header">
        <button type="button" class="btn btn-link categorias-volver p-0" @click="$router.back()">
          <span aria-hidden="true">‹</span>
          <span class="visually-hidden">Volver</span>
        </button>

        <div class="categorias-header-texto">
          <h1 class="categorias-titulo mb-1">{{ productoActual?.nombre || 'Categorías' }}</h1>

          <p class="categorias-subtitulo mb-0 text-muted" v-if="fechaEvento || ciudadEvento">
            <span v-if="fechaEvento">{{ fechaEvento }}</span>
            <span v-if="fechaEvento && ciudadEvento"> · </span>
            <span v-if="ciudadEvento">{{ ciudadEvento }}</span>
          </p>

          <p class="categorias-subtitulo-2 mb-0" v-if="estadioEvento">
            {{ estadioEvento }}
          </p>
        </div>
      </header>
    </section>

    <section class="container pb-4">
      <div v-if="catalogStore.isLoadingCategories">
        <AppLoader variant="skeleton-categorias" :count="8" />
      </div>

      <div v-else-if="errorCategorias" class="alert alert-warning border" role="alert">
        {{ errorCategorias }}
      </div>

      <div v-else-if="categoriasOrdenadas.length" class="categorias-grid">
        <TransitionGroup name="anim-stagger" tag="div" class="categorias-grid-inner">
          <article
            v-for="(categoria, indice) in categoriasOrdenadas"
            :key="categoria.id"
            class="categoria-tarjeta anim-hover-scale"
            :class="{
              'categoria-tarjeta-agotada': !esCategoriaDisponible(categoria),
              'categoria-tarjeta-stock-bajo': esStockBajo(categoria) && esCategoriaDisponible(categoria),
            }"
            :style="stagger(indice, 65)"
          >
            <button
              type="button"
              class="categoria-tarjeta-boton anim-click-feedback"
              :disabled="!esCategoriaDisponible(categoria)"
              @click="abrirModalCategoria(categoria)"
            >
              <div v-if="bloqueFecha" class="categoria-fecha" aria-hidden="true">
                <div class="categoria-fecha-dia">{{ bloqueFecha.diaNumero }}</div>
                <div class="categoria-fecha-mes">{{ bloqueFecha.mesCorto }}</div>
                <div class="categoria-fecha-semana">{{ bloqueFecha.diaSemana }}</div>
              </div>

              <div class="categoria-col-izquierda">
                <h2 class="categoria-nombre mb-1">{{ categoria.nombre }}</h2>
                <div class="categoria-secundaria" v-if="ciudadEvento || estadioEvento || categoria?.limite_por_usuario">
                  <p class="categoria-secundaria-linea mb-0" v-if="categoria?.limite_por_usuario">
                    Máximo de {{ maximoPorCategoria(categoria) }} por persona
                  </p>
                  <p class="categoria-secundaria-linea mb-0" v-if="estadioEvento">
                    {{ estadioEvento }}
                  </p>
                  <p class="categoria-secundaria-linea mb-0" v-if="ciudadEvento">
                    {{ ciudadEvento }}
                  </p>
                </div>

                <p v-if="textoUrgencia(categoria)" class="categoria-urgencia mb-0">
                  <span class="categoria-urgencia-icono" aria-hidden="true">⏱</span>
                  {{ textoUrgencia(categoria) }}
                </p>
              </div>

              <div class="categoria-col-derecha">
                <span
                  class="badge-estado"
                  :class="{
                    'badge-estado-disponible': esCategoriaDisponible(categoria) && !esStockBajo(categoria),
                    'badge-estado-pocas': esCategoriaDisponible(categoria) && esStockBajo(categoria),
                    'badge-estado-agotado': !esCategoriaDisponible(categoria),
                  }"
                >
                  {{ etiquetaDisponibilidad(categoria) }}
                </span>

                <button
                  type="button"
                  class="categoria-precio-cta anim-click-feedback"
                  :disabled="!esCategoriaDisponible(categoria)"
                  @click.stop="abrirModalCategoria(categoria)"
                >
                  {{ formatearPrecio(categoria) }}
                </button>
              </div>
            </button>
          </article>
        </TransitionGroup>
      </div>

      <div v-else class="alert alert-light border" role="alert">
        Este ticket aún no tiene categorías configuradas.
      </div>
    </section>

    <section
      v-if="!catalogStore.isLoadingCategories && !errorCategorias && categoriasOrdenadas.length"
      class="container pb-5"
    >
      <article class="categorias-contexto-inferior" aria-label="Guía para comprar entradas">
        <div class="categorias-contexto-inferior-intro">
          <p class="categorias-contexto-inferior-kicker mb-2">Guía rápida de compra</p>
          <h2 class="categorias-contexto-inferior-titulo mb-2">{{ tituloContexto }}</h2>
          <p class="categorias-contexto-inferior-texto mb-3">{{ descripcionContexto }}</p>

          <div class="categorias-contexto-badges" role="list" aria-label="Aspectos destacados">
            <span
              v-for="badge in contextoBadges"
              :key="badge"
              class="categorias-contexto-badge"
              role="listitem"
            >
              {{ badge }}
            </span>
          </div>
        </div>

        <div class="categorias-contexto-inferior-grid">
          <article
            v-for="item in contextoGuiaCompra"
            :key="item.titulo"
            class="categorias-contexto-inferior-card"
          >
            <h3 class="categorias-contexto-inferior-card-titulo mb-2">{{ item.titulo }}</h3>
            <p class="categorias-contexto-inferior-card-texto mb-0">{{ item.descripcion }}</p>
          </article>
        </div>

        <div class="categorias-contexto-faq">
          <h3 class="categorias-contexto-faq-titulo mb-2">Preguntas rápidas antes de comprar</h3>
          <div class="categorias-contexto-faq-grid">
            <article
              v-for="item in preguntasRapidas"
              :key="item.pregunta"
              class="categorias-contexto-faq-card"
            >
              <p class="categorias-contexto-faq-pregunta mb-1">{{ item.pregunta }}</p>
              <p class="categorias-contexto-faq-respuesta mb-0">{{ item.respuesta }}</p>
            </article>
          </div>
        </div>
      </article>
    </section>

    <Transition v-bind="transicionModal">
      <div v-if="modalAbierto" class="modal-backdrop-lite" @click.self="cerrarModal">
        <div class="modal-panel">
          <div class="modal-panel-header">
            <div>
              <p class="modal-kicker mb-1">Categoría</p>
              <h2 class="modal-titulo mb-0">{{ categoriaActiva?.nombre }}</h2>
            </div>
            <button type="button" class="btn btn-sm btn-outline-secondary modal-cerrar" @click="cerrarModal">
              Cerrar
            </button>
          </div>

          <div class="modal-panel-body">
            <div class="modal-precio-row">
              <div class="modal-precio">{{ formatearPrecio(categoriaActiva) }}</div>
              <span class="modal-badge" :class="{ 'modal-badge-bajo': esStockBajo(categoriaActiva) }">
                {{ etiquetaDisponibilidad(categoriaActiva) }}
              </span>
            </div>

            <div v-if="categoriaActiva?.descripcion" class="modal-seccion">
              <p class="modal-seccion-titulo mb-1">Detalles</p>
              <p class="text-muted mb-0">{{ categoriaActiva.descripcion }}</p>
            </div>

            <div class="modal-seccion" v-if="categoriaActiva?.limite_por_usuario">
              <p class="modal-seccion-titulo mb-1">Condiciones</p>
              <p class="text-muted mb-0">Máximo {{ maximoPorCategoria(categoriaActiva) }} por persona.</p>
            </div>
          </div>

          <div class="modal-panel-footer">
            <div class="modal-cantidad" v-if="esCategoriaDisponible(categoriaActiva)">
              <button
                type="button"
                class="btn btn-outline-secondary btn-sm modal-cantidad-btn"
                :disabled="cantidadParaCategoria(categoriaActiva) <= 1"
                @click="decrementarCantidad(categoriaActiva)"
              >
                −
              </button>
              <input
                type="number"
                class="form-control form-control-sm modal-cantidad-input text-center"
                :min="1"
                :max="maximoPorCategoria(categoriaActiva) || undefined"
                :value="cantidadParaCategoria(categoriaActiva)"
                @input="(event) => fijarCantidadParaCategoria(categoriaActiva, event.target.value)"
              />
              <button
                type="button"
                class="btn btn-outline-secondary btn-sm modal-cantidad-btn"
                :disabled="cantidadParaCategoria(categoriaActiva) >= maximoPorCategoria(categoriaActiva)"
                @click="incrementarCantidad(categoriaActiva)"
              >
                +
              </button>
            </div>

            <button
              type="button"
              class="btn btn-primary fw-semibold modal-cta"
              :disabled="!esCategoriaDisponible(categoriaActiva)"
              @click="agregarCategoriaAlCarrito"
            >
              Agregar
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>
