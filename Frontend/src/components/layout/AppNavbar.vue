<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { BRANDING } from '../../config/constants'
import { ROUTES, paymentPath, ticketCategoriasPath } from '../../config/routes'
import { NAVBAR_LEGAL_LINKS, NAVBAR_SEARCH_SUGGESTIONS_LIMIT } from '../../config/navbar'
import {
  CHECKOUT_CARD_SCHEMES,
  CHECKOUT_COUNTRIES,
  CHECKOUT_COUNTRY_FALLBACK,
  CHECKOUT_COUNTRY_SUGGESTIONS_LIMIT,
  CHECKOUT_ENV,
  CHECKOUT_LOCALE,
  CHECKOUT_PERSONA_SDK_URL,
  CHECKOUT_POLLING_MS,
  CHECKOUT_WEB_COMPONENTS_URL,
  CHECKOUT_WHATSAPP_NUMERO,
} from '../../config/checkout'
import {
  construirDatosCheckoutCliente,
  construirDatosConfirmacion,
  copiarTextoEnPortapapeles,
  formatearErrorCheckout,
  formatearReferenciaConfirmacion,
  normalizarTexto,
} from '../../utils/checkoutPresentation'
import { loadExternalModule, preloadExternalModule } from '../../utils/externalModuleLoader'
import { construirEnlaceWhatsapp } from '../../utils/whatsapp'
import { crearPedidoCompra } from '../../services/pedidosService'
import {
  crearPagoPedido,
  extractPaymentErrorMessage,
  formatPaymentStatusLabel,
  isPaymentStatusFailed,
  isPaymentStatusSuccessful,
  isPaymentStatusTerminal,
  obtenerEstadoPago,
  requiresPaymentKyc,
} from '../../services/paymentsService'
import { getSdkClient } from '../../services/sdkClient'
import { useAuthStore } from '../../stores/auth'
import { useCatalogStore } from '../../stores/catalog'
import { useCarritoStore } from '../../stores/carrito'

const tiendaAutenticacion = useAuthStore()
const tiendaCatalogo = useCatalogStore()
const tiendaCarrito = useCarritoStore()
const enrutador = useRouter()
const rutaActual = useRoute()

const referenciaContenedorBusqueda = ref(null)
const referenciaColapsoMenu = ref(null)
const referenciaSelectorPais = ref(null)
const referenciaContenedorPago = ref(null)
const terminoBusqueda = ref('')
const menuSugerenciasAbierto = ref(false)
const listaPaisesAbierta = ref(false)
const animarBotonCarrito = ref(false)
const menuMovilAbierto = ref(false)
const panelCarritoAbierto = ref(false)
const pasoPanelCarrito = ref('carrito')

const formularioCompra = ref({
  correoElectronico: '',
  nombreCompleto: '',
  telefono: '',
  pais: '',
  documento: '',
  aceptaTerminos: false,
})

const erroresFormularioCompra = ref({})
const estadoCheckout = ref({
  cargando: false,
  error: '',
  exito: null,
})
const estadoPasarela = ref({
  mensaje: '',
  tipoMensaje: '',
  montando: false,
  consultando: false,
  abriendoKyc: false,
  paymentIdMontado: '',
})
const estadoCopiadoConfirmacion = ref({
  id: false,
  referencia: false,
  paymentId: false,
})

let temporizadorAnimacionCarrito = null
let intervaloAnimacionCarrito = null
let intervaloPago = null
let consultaPagoEnCurso = false
let temporizadorPrecargaModulos = null
const temporizadoresCopiadoConfirmacion = {
  id: null,
  referencia: null,
  paymentId: null,
}

const enlacePanel = computed(() => {
  if (!tiendaAutenticacion.isAuthenticated) return null
  return tiendaAutenticacion.isAdmin
    ? { label: 'Panel Admin', to: ROUTES.adminConfig }
    : { label: 'Mi Panel', to: ROUTES.user }
})

const enInicio = computed(() => rutaActual.path === ROUTES.home)

const terminoRecortado = computed(() => terminoBusqueda.value.trim())

const cantidadItemsCarrito = computed(() => tiendaCarrito.cantidadTotal)

const resumenCarrito = computed(() => ({
  items: tiendaCarrito.cantidadTotal,
  subtotal: tiendaCarrito.subtotal,
  moneda: 'USD',
}))

const cabeceraPanelCarrito = computed(() => {
  if (pasoPanelCarrito.value === 'confirmacion') {
    return {
      titulo: 'Seguimiento de pago',
      subtitulo: 'Revisa el estado de pago y conserva tus datos',
    }
  }

  if (pasoPanelCarrito.value === 'datos') {
    return {
      titulo: 'Finalizar compra',
      subtitulo: 'Completa tu información para crear el pedido',
    }
  }

  if (!resumenCarrito.value.items) {
    return {
      titulo: 'Tus productos',
      subtitulo: 'Agrega entradas para comenzar',
    }
  }

  return {
    titulo: 'Tus productos',
    subtitulo: 'Revisa tus entradas y continúa al siguiente paso',
  }
})

const itemsCarrito = computed(() => tiendaCarrito.items)
const carritoVacio = computed(() => itemsCarrito.value.length === 0)
const productosPorId = computed(() => {
  const mapa = new Map()
  for (const producto of tiendaCatalogo.products) {
    const id = Number(producto?.id)
    if (Number.isFinite(id) && id > 0) {
      mapa.set(id, producto)
    }
  }
  return mapa
})

const sugerenciasTicket = computed(() => {
  const consulta = normalizarTexto(terminoRecortado.value)
  if (!consulta) return []

  return tiendaCatalogo.products
    .filter((ticket) => ticket?.id && normalizarTexto(ticket?.nombre).includes(consulta))
    .sort((a, b) => {
      const nombreA = normalizarTexto(a?.nombre)
      const nombreB = normalizarTexto(b?.nombre)
      const iniciaA = nombreA.startsWith(consulta) ? 0 : 1
      const iniciaB = nombreB.startsWith(consulta) ? 0 : 1
      if (iniciaA !== iniciaB) return iniciaA - iniciaB
      return nombreA.localeCompare(nombreB)
    })
    .slice(0, NAVBAR_SEARCH_SUGGESTIONS_LIMIT)
})

const mostrarMenuSugerencias = computed(() => menuSugerenciasAbierto.value && terminoRecortado.value.length > 0)
const paisesSugeridos = computed(() => {
  const consulta = normalizarTexto(formularioCompra.value.pais)
  if (!consulta) {
    return CHECKOUT_COUNTRIES.slice(0, CHECKOUT_COUNTRY_SUGGESTIONS_LIMIT)
  }

  const filtrados = CHECKOUT_COUNTRIES.filter((pais) => normalizarTexto(pais).includes(consulta))
  if (filtrados.length) {
    return filtrados.slice(0, CHECKOUT_COUNTRY_SUGGESTIONS_LIMIT)
  }

  return [CHECKOUT_COUNTRY_FALLBACK]
})

const datosConfirmacionCompra = computed(() => ({
  id: estadoCheckout.value.exito?.id ?? null,
  referencia: estadoCheckout.value.exito?.referencia || '',
  nombre: estadoCheckout.value.exito?.nombre || '',
  email: estadoCheckout.value.exito?.email || '',
  telefono: estadoCheckout.value.exito?.telefono || '',
  pais: estadoCheckout.value.exito?.pais || '',
  cc: estadoCheckout.value.exito?.cc || '',
  subtotal: Number(estadoCheckout.value.exito?.subtotal || 0),
  currency: String(estadoCheckout.value.exito?.currency || 'USD').trim().toUpperCase() || 'USD',
  paymentId: String(estadoCheckout.value.exito?.paymentId || '').trim(),
  paymentStatus: String(estadoCheckout.value.exito?.paymentStatus || '').trim().toLowerCase(),
  checkout: estadoCheckout.value.exito?.checkout || null,
  kyc: estadoCheckout.value.exito?.kyc || null,
  failureReason: estadoCheckout.value.exito?.failureReason || null,
  supportWhatsapp: String(estadoCheckout.value.exito?.supportWhatsapp || '').replace(/\D/g, ''),
}))

const idConfirmacionVisual = computed(() => {
  const id = Number(datosConfirmacionCompra.value.id)
  if (!Number.isInteger(id) || id <= 0) return 'No disponible'
  return String(id)
})

const referenciaConfirmacionVisual = computed(() => {
  const referencia = String(datosConfirmacionCompra.value.referencia || '').trim()
  if (!referencia) return 'No disponible'
  return formatearReferenciaConfirmacion(referencia)
})

const paymentIdConfirmacionVisual = computed(() => {
  const paymentId = String(datosConfirmacionCompra.value.paymentId || '').trim()
  if (!paymentId) return 'No disponible'
  return paymentId
})

const puedeCopiarIdConfirmacion = computed(() => idConfirmacionVisual.value !== 'No disponible')
const puedeCopiarReferenciaConfirmacion = computed(() => Boolean(datosConfirmacionCompra.value.referencia))
const puedeCopiarPaymentIdConfirmacion = computed(() => paymentIdConfirmacionVisual.value !== 'No disponible')

const estadoPagoNormalizado = computed(() => String(datosConfirmacionCompra.value.paymentStatus || '').trim().toLowerCase())
const estadoPagoLabel = computed(() => formatPaymentStatusLabel(estadoPagoNormalizado.value))
const pagoCompletado = computed(() => isPaymentStatusSuccessful(estadoPagoNormalizado.value))
const pagoFallido = computed(() => isPaymentStatusFailed(estadoPagoNormalizado.value))
const pagoTerminal = computed(() => isPaymentStatusTerminal(estadoPagoNormalizado.value))
const pagoRequiereKyc = computed(() => requiresPaymentKyc(estadoPagoNormalizado.value))

const checkoutDisponible = computed(() => {
  const checkout = datosConfirmacionCompra.value.checkout
  return Boolean(checkout?.publicKey && checkout?.session)
})

const mostrarCheckoutEmbebido = computed(
  () => checkoutDisponible.value && !pagoTerminal.value && !pagoRequiereKyc.value
)

const mostrarPanelKyc = computed(() => {
  const kyc = datosConfirmacionCompra.value.kyc
  return Boolean(kyc?.templateId && kyc?.referenceId && kyc?.environmentId) && pagoRequiereKyc.value
})

const failureReasonVisual = computed(() => {
  const failureReason = datosConfirmacionCompra.value.failureReason
  if (!failureReason || (!failureReason.code && !failureReason.message)) return ''

  const code = String(failureReason.code || '').trim()
  const message = String(failureReason.message || '').trim()

  if (code && message) return `${code} - ${message}`
  return code || message
})

const numeroWhatsappSoporte = computed(() => {
  const candidate = String(
    datosConfirmacionCompra.value.supportWhatsapp || CHECKOUT_WHATSAPP_NUMERO || ''
  )
  return candidate.replace(/\D/g, '')
})

const enlaceWhatsappSoporte = computed(() => {
  const numeroWhatsapp = numeroWhatsappSoporte.value
  if (!numeroWhatsapp) return ''

  const idPedido = idConfirmacionVisual.value
  const referenciaPedido = referenciaConfirmacionVisual.value
  const paymentId = paymentIdConfirmacionVisual.value
  const estadoPago = estadoPagoLabel.value
  const subtotalPedido = `${formatearDinero(datosConfirmacionCompra.value.subtotal)} ${datosConfirmacionCompra.value.currency}`

  const mensaje = [
    'Hola, necesito soporte con mi compra en Tickets.',
    '',
    'Datos de seguimiento:',
    `- Pedido ID: ${idPedido}`,
    `- Referencia: ${referenciaPedido}`,
    `- Payment ID: ${paymentId}`,
    `- Estado de pago: ${estadoPago}`,
    `- Total: ${subtotalPedido}`,
  ].join('\n')

  return construirEnlaceWhatsapp(numeroWhatsapp, mensaje)
})

const puedeContactarSoporteWhatsapp = computed(() => Boolean(enlaceWhatsappSoporte.value))

const tituloConfirmacionPago = computed(() => {
  if (pagoCompletado.value) return 'Pago confirmado'
  if (pagoFallido.value) return 'No pudimos completar el pago'
  if (pagoRequiereKyc.value) return 'Verificacion requerida para continuar'
  return 'Pedido creado y pago en proceso'
})

const subtituloConfirmacionPago = computed(() => {
  if (pagoCompletado.value) {
    return 'Tu pedido fue pagado correctamente. Conserva los datos de esta compra.'
  }

  if (pagoFallido.value) {
    return 'El procesador rechazo la transaccion. Puedes reintentar o contactar soporte.'
  }

  if (pagoRequiereKyc.value) {
    return 'Debes completar la validacion de identidad para continuar el pago.'
  }

  return 'Completa la pasarela embebida y revisa el estado en tiempo real.'
})

function activarFeedbackCopiado(clave) {
  estadoCopiadoConfirmacion.value = {
    ...estadoCopiadoConfirmacion.value,
    [clave]: true,
  }

  if (temporizadoresCopiadoConfirmacion[clave]) {
    clearTimeout(temporizadoresCopiadoConfirmacion[clave])
  }

  temporizadoresCopiadoConfirmacion[clave] = setTimeout(() => {
    estadoCopiadoConfirmacion.value = {
      ...estadoCopiadoConfirmacion.value,
      [clave]: false,
    }
    temporizadoresCopiadoConfirmacion[clave] = null
  }, 1800)
}

async function copiarDatoConfirmacion(clave, valor) {
  const copiado = await copiarTextoEnPortapapeles(valor)
  if (!copiado) return
  activarFeedbackCopiado(clave)
}

function setMensajePasarela(mensaje, tipo = '') {
  estadoPasarela.value = {
    ...estadoPasarela.value,
    mensaje: String(mensaje || '').trim(),
    tipoMensaje: String(tipo || '').trim().toLowerCase(),
  }
}

function limpiarMensajePasarela() {
  estadoPasarela.value = {
    ...estadoPasarela.value,
    mensaje: '',
    tipoMensaje: '',
  }
}

function limpiarCheckoutMontado() {
  const contenedor = referenciaContenedorPago.value
  if (contenedor) {
    contenedor.innerHTML = ''
  }

  estadoPasarela.value = {
    ...estadoPasarela.value,
    paymentIdMontado: '',
  }
}

function detenerPollingPago() {
  if (intervaloPago) {
    clearInterval(intervaloPago)
    intervaloPago = null
  }
}

function inferirEntornoCheckout(publicKey) {
  const key = String(publicKey || '').trim()
  if (!key) return CHECKOUT_ENV
  return CHECKOUT_ENV
}

function aplicarRespuestaPagoEnConfirmacion(pagoResponse) {
  if (!estadoCheckout.value.exito) return

  estadoCheckout.value = {
    ...estadoCheckout.value,
    exito: construirDatosConfirmacion({
      pedidoBase: estadoCheckout.value.exito,
      pago: pagoResponse,
      supportWhatsappFallback: CHECKOUT_WHATSAPP_NUMERO,
    }),
  }

  const estado = String(pagoResponse?.status || '').trim().toLowerCase()
  if (isPaymentStatusSuccessful(estado)) {
    setMensajePasarela('Pago confirmado correctamente.', 'ok')
  } else if (isPaymentStatusFailed(estado)) {
    const detalle = String(pagoResponse?.failureReason?.message || '').trim()
    setMensajePasarela(
      detalle ? `Pago rechazado: ${detalle}` : 'El pago fue rechazado por el procesador.',
      'err'
    )
  } else if (requiresPaymentKyc(estado)) {
    setMensajePasarela('Debes completar la verificacion KYC para continuar.', '')
  } else if (estado) {
    setMensajePasarela(`Estado actual del pago: ${formatPaymentStatusLabel(estado)}.`, '')
  }

  if (!mostrarCheckoutEmbebido.value) {
    limpiarCheckoutMontado()
  }
}

async function consultarEstadoPago({ mostrarError = true } = {}) {
  const exito = estadoCheckout.value.exito
  if (!exito?.paymentId || consultaPagoEnCurso) return null

  consultaPagoEnCurso = true
  estadoPasarela.value = {
    ...estadoPasarela.value,
    consultando: true,
  }

  try {
    const pago = await obtenerEstadoPago({
      paymentId: exito.paymentId,
      pedidoId: exito.id,
      referencia: exito.referencia,
      syncOrder: true,
    })

    aplicarRespuestaPagoEnConfirmacion(pago)

    if (isPaymentStatusTerminal(pago.status)) {
      detenerPollingPago()
    }

    await montarCheckoutSiAplica()
    iniciarPollingPagoSiAplica()
    return pago
  } catch (error) {
    if (mostrarError) {
      setMensajePasarela(extractPaymentErrorMessage(error, 'No se pudo consultar el estado del pago.'), 'err')
    }
    return null
  } finally {
    consultaPagoEnCurso = false
    estadoPasarela.value = {
      ...estadoPasarela.value,
      consultando: false,
    }
  }
}

function iniciarPollingPagoSiAplica() {
  if (!panelCarritoAbierto.value) return
  if (!datosConfirmacionCompra.value.paymentId) return
  if (pagoTerminal.value) {
    detenerPollingPago()
    return
  }
  if (intervaloPago) return

  intervaloPago = setInterval(() => {
    void consultarEstadoPago({ mostrarError: false })
  }, CHECKOUT_POLLING_MS)
}

async function montarCheckoutSiAplica() {
  if (!panelCarritoAbierto.value) return
  if (!mostrarCheckoutEmbebido.value) return

  const exito = estadoCheckout.value.exito
  if (!exito?.paymentId) return
  if (estadoPasarela.value.paymentIdMontado === exito.paymentId) return

  const checkout = exito.checkout
  if (!checkout?.publicKey || !checkout?.session) return

  await nextTick()

  const contenedor = referenciaContenedorPago.value
  if (!contenedor) return

  estadoPasarela.value = {
    ...estadoPasarela.value,
    montando: true,
  }

  try {
    if (!CHECKOUT_WEB_COMPONENTS_URL) {
      throw new Error('Falta configurar VITE_CHECKOUT_WEB_COMPONENTS_URL')
    }

    const checkoutModule = await loadExternalModule(CHECKOUT_WEB_COMPONENTS_URL)
    const loadCheckoutWebComponents = checkoutModule?.loadCheckoutWebComponents

    if (typeof loadCheckoutWebComponents !== 'function') {
      throw new Error('No se pudo inicializar Checkout.com Web Components')
    }

    limpiarCheckoutMontado()

    const customerData = construirDatosCheckoutCliente({
      nombre: datosConfirmacionCompra.value.nombre || formularioCompra.value.nombreCompleto,
      correo: datosConfirmacionCompra.value.email || formularioCompra.value.correoElectronico,
      telefono: datosConfirmacionCompra.value.telefono || formularioCompra.value.telefono,
    })
    const entorno = inferirEntornoCheckout(checkout.publicKey)

    const widget = await loadCheckoutWebComponents({
      publicKey: checkout.publicKey,
      paymentSession: checkout.session,
      environment: entorno,
      locale: CHECKOUT_LOCALE,
      componentOptions: {
        data: customerData,
        authentication: {
          required: true,
          data: {
            email: customerData.email,
          },
        },
        flow: {
          data: customerData,
          expandFirstPaymentMethod: true,
          acceptedCardSchemes: CHECKOUT_CARD_SCHEMES,
        },
        card: {
          data: customerData,
          displayCardholderName: 'top',
          acceptedCardSchemes: CHECKOUT_CARD_SCHEMES,
        },
      },
      appearance: {
        colorBorder: '#d7dce5',
        colorAction: '#111827',
        borderRadius: ['12px', '20px'],
      },
      onReady: () => {
        setMensajePasarela('Pasarela lista. Completa tu pago para continuar.', '')
      },
      onPaymentCompleted: async () => {
        setMensajePasarela('Pago enviado. Validando estado...', '')
        await consultarEstadoPago({ mostrarError: false })
      },
      onError: async (_component, error) => {
        const checkoutError = formatearErrorCheckout(error)
        const codigos = checkoutError.joinedCodes ? ` [${checkoutError.joinedCodes}]` : ''
        const hint = checkoutError.hint ? ` ${checkoutError.hint}` : ''
        setMensajePasarela(`Error de checkout: ${checkoutError.message}${codigos}${hint}`, 'err')
        await consultarEstadoPago({ mostrarError: false })
      },
    })

    widget.create('flow').mount('#checkout-payment-container')
    estadoPasarela.value = {
      ...estadoPasarela.value,
      paymentIdMontado: exito.paymentId,
    }
  } catch (error) {
    setMensajePasarela(
      extractPaymentErrorMessage(error, 'No se pudo cargar la pasarela de pago. Intenta de nuevo.'),
      'err'
    )
  } finally {
    estadoPasarela.value = {
      ...estadoPasarela.value,
      montando: false,
    }
  }
}

async function abrirKycManual() {
  if (!mostrarPanelKyc.value || estadoPasarela.value.abriendoKyc) return

  const kyc = datosConfirmacionCompra.value.kyc
  if (!kyc?.templateId || !kyc?.referenceId || !kyc?.environmentId) {
    setMensajePasarela('No hay configuracion KYC disponible para este pago.', 'err')
    return
  }

  estadoPasarela.value = {
    ...estadoPasarela.value,
    abriendoKyc: true,
  }

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
        setMensajePasarela('KYC completado. Verificando estado del pago...', '')
        await consultarEstadoPago({ mostrarError: false })
      },
      onError: (error) => {
        setMensajePasarela(`Error en KYC: ${String(error?.message || error || 'desconocido')}`, 'err')
      },
    })
  } catch (error) {
    setMensajePasarela(extractPaymentErrorMessage(error, 'No se pudo abrir el flujo KYC.'), 'err')
  } finally {
    estadoPasarela.value = {
      ...estadoPasarela.value,
      abriendoKyc: false,
    }
  }
}

function precargarModulosCheckoutEnIdle() {
  const precargar = () => {
    preloadExternalModule(CHECKOUT_WEB_COMPONENTS_URL)
    preloadExternalModule(CHECKOUT_PERSONA_SDK_URL)
  }

  if (typeof window !== 'undefined' && typeof window.requestIdleCallback === 'function') {
    window.requestIdleCallback(precargar, { timeout: 1500 })
    return
  }

  temporizadorPrecargaModulos = setTimeout(precargar, 450)
}

async function prepararPanelConfirmacion({ sincronizar = false } = {}) {
  await nextTick()

  if (sincronizar) {
    await consultarEstadoPago({ mostrarError: false })
  } else {
    await montarCheckoutSiAplica()
    iniciarPollingPagoSiAplica()
  }
}

async function asegurarProductosCargados() {
  if (tiendaCatalogo.products.length || tiendaCatalogo.isLoadingProducts) return
  await tiendaCatalogo.loadProducts()
}

function onFocusBusqueda() {
  menuSugerenciasAbierto.value = true
  asegurarProductosCargados()
}

function onInputBusqueda() {
  menuSugerenciasAbierto.value = true
  asegurarProductosCargados()
}

function limpiarBusqueda() {
  terminoBusqueda.value = ''
  menuSugerenciasAbierto.value = false
}

function irATicket(ticketId) {
  if (!ticketId) return
  enrutador.push(ticketCategoriasPath(ticketId))
  terminoBusqueda.value = ''
  menuSugerenciasAbierto.value = false
}

function onSubmitBusqueda() {
  if (!terminoRecortado.value) return
  const primeraSugerencia = sugerenciasTicket.value[0]
  if (primeraSugerencia) {
    irATicket(primeraSugerencia.id)
    return
  }
  menuSugerenciasAbierto.value = true
}

function manejarClickFuera(event) {
  const contenedorBusqueda = referenciaContenedorBusqueda.value
  if (contenedorBusqueda && !contenedorBusqueda.contains(event.target)) {
    menuSugerenciasAbierto.value = false
  }

  const contenedorPais = referenciaSelectorPais.value
  if (contenedorPais && !contenedorPais.contains(event.target)) {
    listaPaisesAbierta.value = false
  }
}

function manejarTeclaGlobal(event) {
  if (event.key !== 'Escape') return
  menuSugerenciasAbierto.value = false
  cerrarPanelCarrito()
}

function manejarAperturaMenuMovil() {
  menuMovilAbierto.value = true
}

function manejarCierreMenuMovil() {
  menuMovilAbierto.value = false
}

function abrirListaPaises() {
  listaPaisesAbierta.value = true
}

function cerrarListaPaises() {
  listaPaisesAbierta.value = false
}

function onInputPais() {
  listaPaisesAbierta.value = true
  if (erroresFormularioCompra.value.pais) {
    erroresFormularioCompra.value.pais = ''
  }
}

function seleccionarPais(pais) {
  formularioCompra.value.pais = pais
  listaPaisesAbierta.value = false
  if (erroresFormularioCompra.value.pais) {
    erroresFormularioCompra.value.pais = ''
  }
}

function calcularMaximoPermitidoCategoria(categoria) {
  const stock = Number(categoria?.unidades_disponibles || 0)
  if (!stock || stock <= 0) return null
  const limiteUsuario = Number(categoria?.limite_por_usuario || 0)
  if (limiteUsuario > 0) {
    return Math.min(stock, limiteUsuario)
  }
  return stock
}

async function completarDatosEventosEnCarrito() {
  const itemsConDatosFaltantes = itemsCarrito.value.filter(
    (item) =>
      item?.idCategoria &&
      (!item.nombreEvento || !item.fechaEvento || !item.maximoPermitido || !item.idProducto)
  )
  if (!itemsConDatosFaltantes.length) return

  await asegurarProductosCargados()

  const sdk = getSdkClient()
  const cacheProductos = new Map(productosPorId.value)

  for (const item of itemsConDatosFaltantes) {
    try {
      let idProducto = Number(item.idProducto || 0)
      let nombreEvento = item.nombreEvento || ''
      let fechaEvento = item.fechaEvento || ''
      let nombreCategoria = item.nombreCategoria || ''
      let maximoPermitido = Number(item.maximoPermitido || 0) || null

      const requiereCategoria = !idProducto || !nombreCategoria || !maximoPermitido
      if (requiereCategoria) {
        const categoria = await sdk.categorias.get(item.idCategoria)
        idProducto = idProducto || Number(categoria?.producto_id || 0)
        nombreCategoria = nombreCategoria || categoria?.nombre || ''
        maximoPermitido = maximoPermitido || calcularMaximoPermitidoCategoria(categoria)
      }

      if (Number.isFinite(idProducto) && idProducto > 0) {
        if (!cacheProductos.has(idProducto)) {
          const producto = await sdk.productos.get(idProducto)
          cacheProductos.set(idProducto, producto)
        }

        const producto = cacheProductos.get(idProducto)
        nombreEvento = nombreEvento || producto?.nombre || ''
        fechaEvento = fechaEvento || producto?.fecha || ''
      }

      tiendaCarrito.actualizarMetadatosItem(item.idCategoria, {
        idProducto,
        nombreEvento,
        nombreCategoria,
        fechaEvento,
        maximoPermitido,
      })
    } catch {
    }
  }
}

onMounted(() => {
  document.addEventListener('click', manejarClickFuera)
  document.addEventListener('keydown', manejarTeclaGlobal)
  tiendaCarrito.inicializar()
  completarDatosEventosEnCarrito()
  intervaloAnimacionCarrito = setInterval(() => {
    activarAnimacionCarrito()
  }, 3000)

  const nodoColapso = referenciaColapsoMenu.value
  if (nodoColapso) {
    nodoColapso.addEventListener('show.bs.collapse', manejarAperturaMenuMovil)
    nodoColapso.addEventListener('hidden.bs.collapse', manejarCierreMenuMovil)
  }

  precargarModulosCheckoutEnIdle()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', manejarClickFuera)
  document.removeEventListener('keydown', manejarTeclaGlobal)
  if (temporizadorAnimacionCarrito) {
    clearTimeout(temporizadorAnimacionCarrito)
    temporizadorAnimacionCarrito = null
  }
  if (intervaloAnimacionCarrito) {
    clearInterval(intervaloAnimacionCarrito)
    intervaloAnimacionCarrito = null
  }

  if (temporizadorPrecargaModulos) {
    clearTimeout(temporizadorPrecargaModulos)
    temporizadorPrecargaModulos = null
  }

  if (temporizadoresCopiadoConfirmacion.id) {
    clearTimeout(temporizadoresCopiadoConfirmacion.id)
    temporizadoresCopiadoConfirmacion.id = null
  }

  if (temporizadoresCopiadoConfirmacion.referencia) {
    clearTimeout(temporizadoresCopiadoConfirmacion.referencia)
    temporizadoresCopiadoConfirmacion.referencia = null
  }

  if (temporizadoresCopiadoConfirmacion.paymentId) {
    clearTimeout(temporizadoresCopiadoConfirmacion.paymentId)
    temporizadoresCopiadoConfirmacion.paymentId = null
  }

  detenerPollingPago()
  limpiarCheckoutMontado()

  const nodoColapso = referenciaColapsoMenu.value
  if (nodoColapso) {
    nodoColapso.removeEventListener('show.bs.collapse', manejarAperturaMenuMovil)
    nodoColapso.removeEventListener('hidden.bs.collapse', manejarCierreMenuMovil)
  }

  document.body.classList.remove('carrito-bloqueo-scroll')
})

watch(
  () => rutaActual.fullPath,
  () => {
    menuSugerenciasAbierto.value = false
    menuMovilAbierto.value = false
  }
)

watch(panelCarritoAbierto, (abierto) => {
  document.body.classList.toggle('carrito-bloqueo-scroll', abierto)

  if (!abierto) {
    detenerPollingPago()
    limpiarCheckoutMontado()
    return
  }

  if (pasoPanelCarrito.value === 'confirmacion' && estadoCheckout.value.exito) {
    void prepararPanelConfirmacion({ sincronizar: false })
  }
})

function onLogout() {
  tiendaAutenticacion.logout()
}

function formatearDinero(valor) {
  const numero = Number(valor || 0)
  return numero.toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatearFechaEvento(valor) {
  if (!valor) return ''
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return ''

  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
  }).format(fecha)
}

function obtenerNombreEventoItem(item) {
  if (item?.nombreEvento) return item.nombreEvento

  const idProducto = Number(item?.idProducto || 0)
  if (Number.isFinite(idProducto) && idProducto > 0) {
    return productosPorId.value.get(idProducto)?.nombre || ''
  }

  return ''
}

function obtenerFechaEventoItem(item) {
  if (item?.fechaEvento) return item.fechaEvento

  const idProducto = Number(item?.idProducto || 0)
  if (Number.isFinite(idProducto) && idProducto > 0) {
    return productosPorId.value.get(idProducto)?.fecha || ''
  }

  return ''
}

function obtenerMaximoItem(item) {
  const maximo = Number(item?.maximoPermitido || 0)
  if (Number.isNaN(maximo) || maximo <= 0) return null
  return maximo
}

function puedeIncrementarItem(item) {
  const maximo = obtenerMaximoItem(item)
  if (!maximo) return true
  return Number(item?.cantidad || 0) < maximo
}

function textoLimiteItem(item) {
  const maximo = obtenerMaximoItem(item)
  if (!maximo) return ''
  return `Máximo ${maximo} por persona`
}

function activarAnimacionCarrito() {
  animarBotonCarrito.value = true
  if (temporizadorAnimacionCarrito) {
    clearTimeout(temporizadorAnimacionCarrito)
  }

  temporizadorAnimacionCarrito = setTimeout(() => {
    animarBotonCarrito.value = false
    temporizadorAnimacionCarrito = null
  }, 420)
}

function abrirPanelCarrito() {
  activarAnimacionCarrito()
  completarDatosEventosEnCarrito()
  panelCarritoAbierto.value = true

  if (estadoCheckout.value.exito) {
    pasoPanelCarrito.value = 'confirmacion'
    void prepararPanelConfirmacion({ sincronizar: true })
    return
  }

  if (carritoVacio.value) {
    pasoPanelCarrito.value = 'carrito'
  }
}

function cerrarPanelCarrito() {
  panelCarritoAbierto.value = false
  pasoPanelCarrito.value = 'carrito'
  listaPaisesAbierta.value = false
  erroresFormularioCompra.value = {}
  estadoCheckout.value.error = ''
  limpiarMensajePasarela()
}

function abrirPasoDatosCompra() {
  if (carritoVacio.value) return
  estadoCheckout.value.error = ''
  estadoCheckout.value.exito = null
  detenerPollingPago()
  limpiarCheckoutMontado()
  limpiarMensajePasarela()
  pasoPanelCarrito.value = 'datos'
}

function volverAPasoCarrito() {
  pasoPanelCarrito.value = 'carrito'
}

function cerrarConfirmacionCompra() {
  detenerPollingPago()
  limpiarCheckoutMontado()
  limpiarMensajePasarela()

  estadoCopiadoConfirmacion.value = {
    id: false,
    referencia: false,
    paymentId: false,
  }
  estadoCheckout.value.exito = null
  estadoCheckout.value.error = ''
  pasoPanelCarrito.value = 'carrito'
}

function limpiarFormularioCompra() {
  formularioCompra.value = {
    correoElectronico: '',
    nombreCompleto: '',
    telefono: '',
    pais: '',
    documento: '',
    aceptaTerminos: false,
  }
  listaPaisesAbierta.value = false
  erroresFormularioCompra.value = {}
}

function validarFormularioCompra() {
  const errores = {}
  const correo = formularioCompra.value.correoElectronico.trim()
  const nombre = formularioCompra.value.nombreCompleto.trim()
  const telefono = formularioCompra.value.telefono.trim()
  const pais = formularioCompra.value.pais.trim()
  const documento = formularioCompra.value.documento.trim()

  if (!nombre) {
    errores.nombreCompleto = 'Ingresa tu nombre completo.'
  }

  const patronCorreo = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!correo || !patronCorreo.test(correo)) {
    errores.correoElectronico = 'Ingresa un correo válido.'
  }

  if (!telefono) {
    errores.telefono = 'Ingresa tu teléfono de contacto.'
  }

  if (!pais) {
    errores.pais = 'Ingresa tu país.'
  } else {
    const paisCanonico = CHECKOUT_COUNTRIES.find(
      (item) => normalizarTexto(item) === normalizarTexto(pais)
    )
    if (!paisCanonico) {
      errores.pais = 'Pais incorrecto. Debes seleccionar un pais de la lista.'
    } else {
      formularioCompra.value.pais = paisCanonico
    }
  }

  if (!documento) {
    errores.documento = 'Ingresa tu documento.'
  }

  if (!formularioCompra.value.aceptaTerminos) {
    errores.aceptaTerminos = 'Debes aceptar los términos y condiciones.'
  }

  erroresFormularioCompra.value = errores
  return Object.keys(errores).length === 0
}

function obtenerDetallePedidoDesdeCarrito() {
  return itemsCarrito.value.map((item) => ({
    categoria_id: item.idCategoria,
    cantidad: item.cantidad,
  }))
}

async function confirmarCompra() {
  if (estadoCheckout.value.cargando) return
  if (carritoVacio.value) {
    pasoPanelCarrito.value = 'carrito'
    return
  }

  if (!validarFormularioCompra()) return

  detenerPollingPago()
  limpiarCheckoutMontado()
  limpiarMensajePasarela()
  consultaPagoEnCurso = false

  estadoCheckout.value = {
    cargando: true,
    error: '',
    exito: null,
  }
  estadoCopiadoConfirmacion.value = {
    id: false,
    referencia: false,
    paymentId: false,
  }

  try {
    const pedidoCreado = await crearPedidoCompra({
      correo_electronico: formularioCompra.value.correoElectronico,
      nombre_completo: formularioCompra.value.nombreCompleto,
      telefono: formularioCompra.value.telefono,
      pais: formularioCompra.value.pais,
      documento: formularioCompra.value.documento,
      acepta_terminos: formularioCompra.value.aceptaTerminos,
      detalles: obtenerDetallePedidoDesdeCarrito(),
    })

    const idPedidoCreado = Number(pedidoCreado?.id)
    const totalPedidoCreado = Number(pedidoCreado?.total)
    const subtotalConfirmacion = Number.isFinite(totalPedidoCreado)
      ? totalPedidoCreado
      : Number(resumenCarrito.value.subtotal || 0)

    const pedidoBase = {
      id: Number.isInteger(idPedidoCreado) && idPedidoCreado > 0 ? idPedidoCreado : null,
      referencia: String(pedidoCreado?.referencia || '').trim(),
      nombre: String(pedidoCreado?.nombre_completo || formularioCompra.value.nombreCompleto || '').trim(),
      email: String(pedidoCreado?.correo_electronico || formularioCompra.value.correoElectronico || '').trim(),
      telefono: String(pedidoCreado?.telefono || formularioCompra.value.telefono || '').trim(),
      pais: String(pedidoCreado?.pais || formularioCompra.value.pais || '').trim(),
      cc: String(pedidoCreado?.documento || formularioCompra.value.documento || '').trim(),
      subtotal: Number.isFinite(subtotalConfirmacion) ? subtotalConfirmacion : 0,
      currency: 'USD',
      paymentId: '',
      paymentStatus: '',
      checkout: null,
      kyc: null,
      failureReason: null,
      supportWhatsapp: String(CHECKOUT_WHATSAPP_NUMERO || '').replace(/\D/g, ''),
      updatedAt: '',
    }

    if (!pedidoBase.id) {
      throw new Error('El pedido fue creado sin un ID valido.')
    }

    let pagoCreado = null
    try {
      pagoCreado = await crearPagoPedido({
        pedidoId: pedidoBase.id,
        referencia: pedidoBase.referencia,
        aceptaTerminos: formularioCompra.value.aceptaTerminos,
      })
    } catch (errorPago) {
      estadoCheckout.value = {
        cargando: false,
        error: '',
        exito: construirDatosConfirmacion({
          pedidoBase,
          pago: null,
        }),
      }

      const mensajePasarela = extractPaymentErrorMessage(
        errorPago,
        'intenta nuevamente en unos minutos.'
      )
      const mensajePasarelaNormalizado = String(mensajePasarela || '').trim().toLowerCase()
      const esPasarelaTemporalmenteNoDisponible = mensajePasarelaNormalizado.includes(
        'pasarela de pago no se encuentra habilitada temporalmente'
      )

      setMensajePasarela(
        esPasarelaTemporalmenteNoDisponible
          ? `Pedido creado correctamente. ${mensajePasarela}`
          : `Pedido creado, pero no se pudo iniciar la pasarela: ${mensajePasarela}`,
        'err'
      )

      tiendaCarrito.vaciar()
      limpiarFormularioCompra()
      pasoPanelCarrito.value = 'confirmacion'
      await prepararPanelConfirmacion({ sincronizar: false })
      return
    }

    estadoCheckout.value = {
      cargando: false,
      error: '',
      exito: construirDatosConfirmacion({
        pedidoBase,
        pago: pagoCreado,
      }),
    }

    aplicarRespuestaPagoEnConfirmacion(pagoCreado)

    tiendaCarrito.vaciar()
    limpiarFormularioCompra()

    const paymentToken = String(pagoCreado?.paymentToken || '').trim()
    if (paymentToken) {
      cerrarPanelCarrito()
      await enrutador.push(paymentPath(paymentToken))
      return
    }

    pasoPanelCarrito.value = 'confirmacion'
    await prepararPanelConfirmacion({ sincronizar: false })
  } catch (error) {
    estadoCheckout.value = {
      cargando: false,
      error: error?.message || 'No se pudo crear el pedido. Intenta de nuevo.',
      exito: null,
    }
  }
}

function actualizarCantidadItem(idCategoria, valor) {
  tiendaCarrito.actualizarCantidad(idCategoria, valor)
}

function decrementarCantidadItem(idCategoria) {
  tiendaCarrito.decrementarCantidad(idCategoria)
}

function incrementarCantidadItem(idCategoria) {
  const item = itemsCarrito.value.find((valor) => valor.idCategoria === idCategoria)
  if (!item) return
  if (!puedeIncrementarItem(item)) return
  tiendaCarrito.incrementarCantidad(idCategoria)
}

function quitarItem(idCategoria) {
  tiendaCarrito.removerItem(idCategoria)
}
</script>

<template>
  <nav class="navbar navbar-expand-xl navbar-dark app-navbar sticky-top" :class="{ 'app-navbar-overlay': enInicio }">
    <div class="container nav-shell px-3 px-lg-4">
      <div class="nav-principal-barra">
        <RouterLink class="navbar-brand fw-bold nav-brand d-flex align-items-center gap-2" :to="ROUTES.home">
          <img :src="BRANDING.logoPath" alt="Tickets Nova" width="36" height="36" class="rounded-circle" />
          <span>{{ BRANDING.name }}</span>
        </RouterLink>

        <div ref="referenciaContenedorBusqueda" class="navbar-ticket-search nav-search-wrap">
          <form class="navbar-search-box" role="search" @submit.prevent="onSubmitBusqueda">
            <span class="navbar-search-icon" aria-hidden="true">⌕</span>
            <input
              v-model.trim="terminoBusqueda"
              class="navbar-search-input"
              type="search"
              placeholder="Buscar ticket"
              aria-label="Buscar ticket"
              autocomplete="off"
              @focus="onFocusBusqueda"
              @input="onInputBusqueda"
            />
            <button
              v-if="terminoBusqueda"
              class="navbar-search-clear"
              type="button"
              aria-label="Limpiar búsqueda"
              @click="limpiarBusqueda"
            >
              ×
            </button>
          </form>

          <div v-if="mostrarMenuSugerencias" class="navbar-search-dropdown">
            <p class="navbar-search-label mb-1">Búsquedas parecidas</p>

            <button
              v-for="ticket in sugerenciasTicket"
              :key="ticket.id"
              class="navbar-search-item"
              type="button"
              @mousedown.prevent="irATicket(ticket.id)"
            >
              <span class="navbar-search-item-icon" aria-hidden="true">⌕</span>
              <span class="navbar-search-item-text">{{ ticket.nombre }}</span>
            </button>

            <p v-if="!sugerenciasTicket.length" class="navbar-search-empty mb-0">
              No encontramos tickets similares.
            </p>
          </div>
        </div>

        <div class="nav-principal-derecha">
          <nav class="nav-enlaces-rapidos d-none d-xl-flex" aria-label="Enlaces principales">
            <RouterLink
              v-for="item in NAVBAR_LEGAL_LINKS"
              :key="`desktop-${item.to}`"
              class="nav-link nav-link-rapido"
              :to="item.to"
            >
              {{ item.label }}
            </RouterLink>
          </nav>

          <div class="nav-meta-usd nav-meta-usd-inline" aria-label="Moneda USD">
            <span>USD</span>
          </div>

          <button
            type="button"
            class="nav-carrito-btn"
            :class="{ 'nav-carrito-btn-animando': animarBotonCarrito }"
            aria-label="Abrir carrito"
            @click="abrirPanelCarrito"
          >
            <svg
              class="nav-carrito-icono"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M3 5H5L7.4 15.5C7.6 16.3 8.3 17 9.2 17H18.1C18.9 17 19.7 16.5 19.9 15.7L21 10.5H8"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <circle cx="10" cy="20" r="1.4" fill="currentColor" />
              <circle cx="18" cy="20" r="1.4" fill="currentColor" />
            </svg>
            <span class="nav-carrito-badge">{{ cantidadItemsCarrito }}</span>
          </button>

          <button
            class="navbar-toggler nav-menu-btn"
            :class="{ 'nav-menu-btn-abierto': menuMovilAbierto }"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#mainNavbar"
            aria-controls="mainNavbar"
            aria-expanded="false"
            aria-label="Mostrar navegación"
          >
            <svg
              class="nav-menu-icono"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <circle cx="12" cy="8" r="3.2" stroke="currentColor" stroke-width="1.8" />
              <path d="M5.8 19.3C6.9 16.9 9.2 15.4 12 15.4C14.8 15.4 17.1 16.9 18.2 19.3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </button>
        </div>
      </div>

      <div
        id="mainNavbar"
        ref="referenciaColapsoMenu"
        class="collapse navbar-collapse align-items-xl-center gap-xl-3 nav-collapse-panel"
      >

        <ul class="navbar-nav align-items-xl-center gap-xl-2 ms-xl-auto">
          <li v-for="item in NAVBAR_LEGAL_LINKS" :key="item.to" class="nav-item d-xl-none nav-colapso-item">
            <RouterLink class="nav-link nav-colapso-link" :to="item.to">{{ item.label }}</RouterLink>
          </li>
          <li v-if="enlacePanel" class="nav-item nav-colapso-item">
            <RouterLink class="btn btn-sm btn-light fw-semibold px-3 nav-colapso-boton nav-colapso-boton-panel" :to="enlacePanel.to">
              {{ enlacePanel.label }}
            </RouterLink>
          </li>
          <li v-if="tiendaAutenticacion.isAuthenticated" class="nav-item nav-colapso-item">
            <button class="btn btn-outline-light btn-sm nav-colapso-boton nav-colapso-boton-sesion" type="button" @click="onLogout">
              Cerrar sesión
            </button>
          </li>
        </ul>
      </div>

    </div>
  </nav>

  <Transition name="anim-panel-carrito">
    <div v-if="panelCarritoAbierto" class="carrito-panel-backdrop" @click.self="cerrarPanelCarrito">
      <aside class="carrito-panel-lateral" role="dialog" aria-modal="true" aria-label="Carrito">
        <header class="carrito-panel-lateral-header">
          <div class="carrito-panel-cabecera-texto">
            <h2 class="carrito-panel-titulo mb-0">{{ cabeceraPanelCarrito.titulo }}</h2>
            <p class="carrito-panel-subtitulo mb-0">{{ cabeceraPanelCarrito.subtitulo }}</p>
          </div>
          <button
            type="button"
            class="btn-close btn-close-white carrito-panel-cerrar"
            aria-label="Cerrar carrito"
            @click="cerrarPanelCarrito"
          />
        </header>

        <div class="carrito-panel-lateral-cuerpo">
          <Transition name="anim-contenido-carrito" mode="out-in">
            <div v-if="pasoPanelCarrito === 'carrito'" key="paso-carrito" class="carrito-panel-scroll">
              <div v-if="carritoVacio" class="carrito-panel-lateral-vacio">
                <p class="mb-1 fw-semibold">Tu carrito está vacío</p>
                <p class="mb-0 text-white-50">Aún no agregaste entradas. Cuando lo hagas, aparecerán aquí.</p>
              </div>

              <div v-else class="carrito-items-lista">
                <article v-for="item in itemsCarrito" :key="item.idCategoria" class="carrito-item-card">
                  <div class="carrito-item-encabezado">
                    <div class="carrito-item-principal">
                      <p class="carrito-item-evento mb-1">{{ obtenerNombreEventoItem(item) || 'Evento' }}</p>
                      <p class="carrito-item-categoria mb-1">{{ item.nombreCategoria }}</p>
                    </div>

                    <p v-if="obtenerFechaEventoItem(item)" class="carrito-item-fecha mb-0">
                      {{ formatearFechaEvento(obtenerFechaEventoItem(item)) }}
                    </p>
                  </div>

                  <div class="carrito-item-fila">
                    <p class="carrito-item-precio mb-0">Precio: {{ formatearDinero(item.precioUnitario) }} USD</p>

                    <div class="carrito-item-controles">
                      <button
                        type="button"
                        class="btn btn-outline-light btn-sm carrito-item-btn"
                        :disabled="item.cantidad <= 1"
                        @click="decrementarCantidadItem(item.idCategoria)"
                      >
                        −
                      </button>

                      <input
                        class="form-control form-control-sm text-center carrito-item-input"
                        type="number"
                        min="0"
                        :max="obtenerMaximoItem(item) || undefined"
                        :value="item.cantidad"
                        @input="(event) => actualizarCantidadItem(item.idCategoria, event.target.value)"
                      />

                      <button
                        type="button"
                        class="btn btn-outline-light btn-sm carrito-item-btn"
                        :disabled="!puedeIncrementarItem(item)"
                        @click="incrementarCantidadItem(item.idCategoria)"
                      >
                        +
                      </button>

                      <button
                        type="button"
                        class="btn btn-link btn-sm carrito-item-eliminar"
                        @click="quitarItem(item.idCategoria)"
                      >
                        Quitar
                      </button>
                    </div>
                  </div>

                  <p v-if="textoLimiteItem(item)" class="carrito-item-limite mb-0">{{ textoLimiteItem(item) }}</p>
                </article>
              </div>
            </div>

            <div v-else-if="pasoPanelCarrito === 'datos'" key="paso-datos" class="carrito-panel-scroll">
              <form class="carrito-formulario" @submit.prevent="confirmarCompra">
                <div class="mb-3">
                  <label class="form-label mb-1" for="compra-nombre">Nombre completo</label>
                  <input
                    id="compra-nombre"
                    v-model.trim="formularioCompra.nombreCompleto"
                    type="text"
                    class="form-control"
                    autocomplete="name"
                    :aria-invalid="Boolean(erroresFormularioCompra.nombreCompleto)"
                  />
                  <small v-if="erroresFormularioCompra.nombreCompleto" class="text-danger">{{ erroresFormularioCompra.nombreCompleto }}</small>
                </div>

                <div class="mb-3">
                  <label class="form-label mb-1" for="compra-correo">Correo electrónico</label>
                  <input
                    id="compra-correo"
                    v-model.trim="formularioCompra.correoElectronico"
                    type="email"
                    class="form-control"
                    autocomplete="email"
                    :aria-invalid="Boolean(erroresFormularioCompra.correoElectronico)"
                  />
                  <small v-if="erroresFormularioCompra.correoElectronico" class="text-danger">{{ erroresFormularioCompra.correoElectronico }}</small>
                </div>

                <div class="mb-3">
                  <label class="form-label mb-1" for="compra-telefono">Teléfono</label>
                  <input
                    id="compra-telefono"
                    v-model.trim="formularioCompra.telefono"
                    type="tel"
                    class="form-control"
                    autocomplete="tel"
                    :aria-invalid="Boolean(erroresFormularioCompra.telefono)"
                  />
                  <small v-if="erroresFormularioCompra.telefono" class="text-danger">{{ erroresFormularioCompra.telefono }}</small>
                </div>

                <div ref="referenciaSelectorPais" class="mb-3 position-relative">
                  <label class="form-label mb-1" for="compra-pais">País</label>
                  <input
                    id="compra-pais"
                    v-model.trim="formularioCompra.pais"
                    type="text"
                    class="form-control"
                    autocomplete="off"
                    :aria-invalid="Boolean(erroresFormularioCompra.pais)"
                    placeholder="Escribe para buscar (si no aparece, elige Otros)"
                    @focus="abrirListaPaises"
                    @input="onInputPais"
                  />
                  <div v-if="listaPaisesAbierta" class="checkout-pais-dropdown">
                    <button
                      v-for="pais in paisesSugeridos"
                      :key="`pais-${pais}`"
                      type="button"
                      class="checkout-pais-opcion"
                      @mousedown.prevent="seleccionarPais(pais)"
                    >
                      {{ pais }}
                    </button>
                    <p v-if="!paisesSugeridos.length" class="checkout-pais-vacio mb-0">
                      No encontramos coincidencias.
                    </p>
                  </div>
                  <small v-if="erroresFormularioCompra.pais" class="text-danger">{{ erroresFormularioCompra.pais }}</small>
                </div>

                <div class="mb-3">
                  <label class="form-label mb-1" for="compra-documento">Documento (CC u otro)</label>
                  <input
                    id="compra-documento"
                    v-model.trim="formularioCompra.documento"
                    type="text"
                    class="form-control"
                    :aria-invalid="Boolean(erroresFormularioCompra.documento)"
                  />
                  <small v-if="erroresFormularioCompra.documento" class="text-danger">{{ erroresFormularioCompra.documento }}</small>
                </div>

                <div class="form-check mb-2">
                  <input
                    id="compra-acepta-terminos"
                    v-model="formularioCompra.aceptaTerminos"
                    class="form-check-input"
                    type="checkbox"
                  />
                  <label class="form-check-label" for="compra-acepta-terminos">
                    Acepto los
                    <RouterLink :to="ROUTES.terminos">términos y condiciones</RouterLink>
                    y la
                    <RouterLink :to="ROUTES.privacidad">política de privacidad</RouterLink>
                    , y autorizo el procesamiento del pago con proveedores integrados como Crossmint
                    para validación transaccional, antifraude y cumplimiento.
                  </label>
                </div>
                <small v-if="erroresFormularioCompra.aceptaTerminos" class="text-danger d-block">
                  {{ erroresFormularioCompra.aceptaTerminos }}
                </small>

                <p v-if="estadoCheckout.error" class="text-danger small mt-3 mb-0">{{ estadoCheckout.error }}</p>
              </form>
            </div>

            <div v-else key="paso-confirmacion" class="carrito-panel-scroll">
              <section class="checkout-confirmacion" aria-live="polite">
                <div
                  class="checkout-confirmacion-icono"
                  :class="{
                    'checkout-confirmacion-icono--ok': pagoCompletado,
                    'checkout-confirmacion-icono--error': pagoFallido,
                    'checkout-confirmacion-icono--pendiente': !pagoCompletado && !pagoFallido,
                  }"
                  aria-hidden="true"
                >
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.7" />
                    <path
                      v-if="pagoFallido"
                      d="M8.5 8.5L15.5 15.5M15.5 8.5L8.5 15.5"
                      stroke="currentColor"
                      stroke-width="2.1"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      v-else
                      d="M7.8 12.4L10.6 15.2L16.4 9.4"
                      stroke="currentColor"
                      stroke-width="2.1"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </div>

                <div class="text-center">
                  <h3 class="checkout-confirmacion-titulo mb-1">{{ tituloConfirmacionPago }}</h3>
                  <p class="checkout-confirmacion-subtitulo mb-2">{{ subtituloConfirmacionPago }}</p>
                  <span class="checkout-confirmacion-badge">{{ estadoPagoLabel }}</span>
                </div>

                <div class="checkout-confirmacion-datos">
                  <article class="checkout-confirmacion-dato checkout-confirmacion-dato-id-principal">
                    <div class="checkout-confirmacion-dato-cabecera">
                      <span class="checkout-confirmacion-dato-etiqueta">ID</span>
                      <button
                        type="button"
                        class="checkout-confirmacion-dato-boton-copiar"
                        :class="{ 'checkout-confirmacion-dato-boton-copiar-activo': estadoCopiadoConfirmacion.id }"
                        :disabled="!puedeCopiarIdConfirmacion"
                        @click="copiarDatoConfirmacion('id', idConfirmacionVisual)"
                      >
                        <svg
                          class="checkout-confirmacion-dato-boton-copiar-icono"
                          viewBox="0 0 24 24"
                          fill="none"
                          xmlns="http://www.w3.org/2000/svg"
                          aria-hidden="true"
                        >
                          <path
                            d="M8.2 8.7V6.9C8.2 5.85 9.05 5 10.1 5H17.1C18.15 5 19 5.85 19 6.9V13.9C19 14.95 18.15 15.8 17.1 15.8H15.3"
                            stroke="currentColor"
                            stroke-width="1.8"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                          />
                          <rect
                            x="5"
                            y="8.2"
                            width="10.8"
                            height="10.8"
                            rx="1.9"
                            stroke="currentColor"
                            stroke-width="1.8"
                          />
                        </svg>
                        <span>{{ estadoCopiadoConfirmacion.id ? 'Copiado' : 'Copiar' }}</span>
                      </button>
                    </div>
                    <strong class="checkout-confirmacion-dato-valor checkout-confirmacion-dato-valor-id">{{ idConfirmacionVisual }}</strong>
                  </article>

                  <article class="checkout-confirmacion-dato">
                    <div class="checkout-confirmacion-dato-cabecera">
                      <span class="checkout-confirmacion-dato-etiqueta">Referencia del pedido</span>
                      <button
                        type="button"
                        class="checkout-confirmacion-dato-boton-copiar"
                        :class="{ 'checkout-confirmacion-dato-boton-copiar-activo': estadoCopiadoConfirmacion.referencia }"
                        :disabled="!puedeCopiarReferenciaConfirmacion"
                        @click="copiarDatoConfirmacion('referencia', datosConfirmacionCompra.referencia)"
                      >
                        <svg
                          class="checkout-confirmacion-dato-boton-copiar-icono"
                          viewBox="0 0 24 24"
                          fill="none"
                          xmlns="http://www.w3.org/2000/svg"
                          aria-hidden="true"
                        >
                          <path
                            d="M8.2 8.7V6.9C8.2 5.85 9.05 5 10.1 5H17.1C18.15 5 19 5.85 19 6.9V13.9C19 14.95 18.15 15.8 17.1 15.8H15.3"
                            stroke="currentColor"
                            stroke-width="1.8"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                          />
                          <rect
                            x="5"
                            y="8.2"
                            width="10.8"
                            height="10.8"
                            rx="1.9"
                            stroke="currentColor"
                            stroke-width="1.8"
                          />
                        </svg>
                        <span>{{ estadoCopiadoConfirmacion.referencia ? 'Copiado' : 'Copiar' }}</span>
                      </button>
                    </div>
                    <strong class="checkout-confirmacion-dato-valor checkout-confirmacion-dato-valor-referencia">
                      {{ referenciaConfirmacionVisual }}
                    </strong>
                  </article>

                  <article class="checkout-confirmacion-dato">
                    <div class="checkout-confirmacion-dato-cabecera">
                      <span class="checkout-confirmacion-dato-etiqueta">Payment ID</span>
                      <button
                        type="button"
                        class="checkout-confirmacion-dato-boton-copiar"
                        :class="{ 'checkout-confirmacion-dato-boton-copiar-activo': estadoCopiadoConfirmacion.paymentId }"
                        :disabled="!puedeCopiarPaymentIdConfirmacion"
                        @click="copiarDatoConfirmacion('paymentId', paymentIdConfirmacionVisual)"
                      >
                        <svg
                          class="checkout-confirmacion-dato-boton-copiar-icono"
                          viewBox="0 0 24 24"
                          fill="none"
                          xmlns="http://www.w3.org/2000/svg"
                          aria-hidden="true"
                        >
                          <path
                            d="M8.2 8.7V6.9C8.2 5.85 9.05 5 10.1 5H17.1C18.15 5 19 5.85 19 6.9V13.9C19 14.95 18.15 15.8 17.1 15.8H15.3"
                            stroke="currentColor"
                            stroke-width="1.8"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                          />
                          <rect
                            x="5"
                            y="8.2"
                            width="10.8"
                            height="10.8"
                            rx="1.9"
                            stroke="currentColor"
                            stroke-width="1.8"
                          />
                        </svg>
                        <span>{{ estadoCopiadoConfirmacion.paymentId ? 'Copiado' : 'Copiar' }}</span>
                      </button>
                    </div>
                    <strong class="checkout-confirmacion-dato-valor checkout-confirmacion-dato-valor-referencia">
                      {{ paymentIdConfirmacionVisual }}
                    </strong>
                  </article>

                  <article class="checkout-confirmacion-dato">
                    <div class="checkout-confirmacion-dato-cabecera">
                      <span class="checkout-confirmacion-dato-etiqueta">Total</span>
                    </div>
                    <strong class="checkout-confirmacion-dato-valor">
                      {{ formatearDinero(datosConfirmacionCompra.subtotal) }} {{ datosConfirmacionCompra.currency }}
                    </strong>
                  </article>
                </div>

                <div class="checkout-confirmacion-mensaje">
                  <p class="mb-2">Guarda tu referencia, ID de pedido y payment ID para soporte y trazabilidad.</p>
                  <p class="mb-0">Si el estado no cambia automaticamente, actualizalo manualmente desde este panel.</p>
                </div>

                <p
                  v-if="estadoPasarela.mensaje"
                  class="checkout-pasarela-alerta mb-0"
                  :class="{
                    'checkout-pasarela-alerta--ok': estadoPasarela.tipoMensaje === 'ok',
                    'checkout-pasarela-alerta--error': estadoPasarela.tipoMensaje === 'err',
                  }"
                >
                  {{ estadoPasarela.mensaje }}
                </p>

                <section v-if="mostrarCheckoutEmbebido" class="checkout-pasarela-panel">
                  <div class="checkout-pasarela-cabecera">
                    <h4 class="checkout-pasarela-titulo mb-0">Pasarela de pago segura</h4>
                    <button
                      type="button"
                      class="btn btn-outline-light btn-sm"
                      :disabled="estadoPasarela.consultando || estadoPasarela.montando"
                      @click="consultarEstadoPago()"
                    >
                      {{ estadoPasarela.consultando ? 'Actualizando...' : 'Actualizar estado' }}
                    </button>
                  </div>

                  <p class="checkout-pasarela-subtitulo mb-0">
                    Completa la tarjeta directamente aqui en entorno productivo y seguro.
                  </p>

                  <div id="checkout-payment-container" ref="referenciaContenedorPago" class="checkout-pasarela-contenedor" />
                </section>

                <section v-if="mostrarPanelKyc" class="checkout-kyc-panel">
                  <h4 class="checkout-kyc-titulo mb-1">Validacion de identidad</h4>
                  <p class="checkout-kyc-texto mb-2">
                    Crossmint solicita KYC para continuar el pago de este pedido.
                  </p>
                  <button
                    type="button"
                    class="btn btn-light btn-sm fw-semibold"
                    :disabled="estadoPasarela.abriendoKyc"
                    @click="abrirKycManual"
                  >
                    {{ estadoPasarela.abriendoKyc ? 'Abriendo KYC...' : 'Abrir KYC' }}
                  </button>
                </section>

                <p v-if="failureReasonVisual" class="checkout-failure-reason mb-0">
                  Motivo reportado por el procesador: {{ failureReasonVisual }}
                </p>

                <a
                  v-if="puedeContactarSoporteWhatsapp"
                  :href="enlaceWhatsappSoporte"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="checkout-boton-whatsapp"
                >
                  <svg
                    class="checkout-boton-whatsapp-icono"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden="true"
                  >
                    <path
                      d="M19.11 4.93A9.77 9.77 0 0 0 12.03 2a9.98 9.98 0 0 0-8.65 15l-1.06 3.87 3.96-1.04a10 10 0 0 0 4.75 1.21h.01A9.99 9.99 0 0 0 21 11.96a9.84 9.84 0 0 0-1.89-7.03ZM12.04 20.2h-.01a8.3 8.3 0 0 1-4.22-1.15l-.3-.18-2.35.62.63-2.29-.2-.32a8.27 8.27 0 0 1-1.28-4.43A8.42 8.42 0 0 1 12.03 3.8c2.24 0 4.33.87 5.91 2.46a8.25 8.25 0 0 1 2.45 5.86 8.4 8.4 0 0 1-8.35 8.08Zm4.57-6.25c-.25-.12-1.47-.72-1.7-.8-.23-.08-.4-.12-.57.13-.17.25-.65.8-.8.96-.15.17-.29.19-.54.06-.25-.12-1.03-.38-1.96-1.2-.72-.64-1.2-1.42-1.34-1.66-.14-.25-.01-.38.11-.5.11-.11.25-.29.37-.43.12-.15.16-.25.25-.42.08-.17.04-.31-.02-.43-.06-.12-.57-1.36-.78-1.86-.2-.48-.41-.42-.57-.42h-.49c-.17 0-.43.06-.66.31-.23.25-.87.85-.87 2.08s.89 2.42 1.01 2.58c.12.17 1.74 2.65 4.21 3.72.59.25 1.05.4 1.41.5.59.19 1.12.17 1.54.1.47-.07 1.47-.6 1.68-1.18.21-.58.21-1.08.15-1.18-.06-.1-.23-.16-.48-.29Z"
                    />
                  </svg>
                  <span>Contactar soporte por WhatsApp</span>
                </a>

                <p v-else class="checkout-whatsapp-no-disponible mb-0">
                  No hay un numero de soporte configurado en este entorno.
                </p>

                <button
                  type="button"
                  class="btn btn-outline-light fw-semibold checkout-confirmacion-secundario"
                  @click="cerrarConfirmacionCompra"
                >
                  {{ pagoCompletado ? 'Cerrar confirmacion' : 'Cerrar y volver al carrito' }}
                </button>
              </section>
            </div>
          </Transition>
        </div>

        <footer v-if="pasoPanelCarrito !== 'confirmacion'" class="carrito-panel-lateral-footer">
          <div class="carrito-panel-lateral-resumen">
            <span>Items</span>
            <strong>{{ resumenCarrito.items }}</strong>
          </div>
          <div class="carrito-panel-lateral-resumen">
            <span>Subtotal</span>
            <strong>{{ formatearDinero(resumenCarrito.subtotal) }} {{ resumenCarrito.moneda }}</strong>
          </div>

          <div class="carrito-panel-acciones">
            <button
              v-if="pasoPanelCarrito === 'datos'"
              type="button"
              class="btn btn-outline-light fw-semibold"
              :disabled="estadoCheckout.cargando"
              @click="volverAPasoCarrito"
            >
              Volver
            </button>

            <button
              v-if="pasoPanelCarrito === 'carrito' && !carritoVacio"
              type="button"
              class="btn btn-light fw-semibold"
              @click="abrirPasoDatosCompra"
            >
              Siguiente
            </button>

            <button
              v-if="pasoPanelCarrito === 'datos'"
              type="button"
              class="btn btn-light fw-semibold"
              :disabled="estadoCheckout.cargando || carritoVacio || !formularioCompra.aceptaTerminos"
              @click="confirmarCompra"
            >
              {{ estadoCheckout.cargando ? 'Confirmando...' : 'Confirmar compra' }}
            </button>
          </div>
        </footer>
      </aside>
    </div>
  </Transition>
</template>
