export function normalizarTexto(value = '') {
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

export function formatearReferenciaConfirmacion(referencia = '') {
  const referenciaLimpia = String(referencia || '').trim().toUpperCase()
  if (!referenciaLimpia) return ''

  const partes = referenciaLimpia.split('-').filter(Boolean)
  if (!partes.length) return referenciaLimpia

  if (partes.length === 1) {
    const bloques = partes[0].match(/.{1,4}/g)
    return bloques ? bloques.join('-') : referenciaLimpia
  }

  const prefijo = partes[0]
  const resto = partes.slice(1).join('').replace(/[^A-Z0-9]/g, '')
  if (!resto) return prefijo

  const bloques = resto.match(/.{1,4}/g)
  if (!bloques) return `${prefijo}-${resto}`

  return `${prefijo}-${bloques.join('-')}`
}

export async function copiarTextoEnPortapapeles(texto) {
  const contenido = String(texto || '').trim()
  if (!contenido) return false

  if (navigator?.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(contenido)
      return true
    } catch {
    }
  }

  try {
    const areaTemporal = document.createElement('textarea')
    areaTemporal.value = contenido
    areaTemporal.setAttribute('readonly', '')
    areaTemporal.style.position = 'fixed'
    areaTemporal.style.opacity = '0'
    document.body.appendChild(areaTemporal)
    areaTemporal.focus()
    areaTemporal.select()
    const resultado = document.execCommand('copy')
    document.body.removeChild(areaTemporal)
    return Boolean(resultado)
  } catch {
    return false
  }
}

export function formatearErrorCheckout(error) {
  const message = String(error?.message || error || 'Error desconocido')
  const details =
    error && typeof error === 'object' && error.details && typeof error.details === 'object'
      ? error.details
      : {}

  const requestCodes = Array.isArray(details.requestErrorCodes)
    ? details.requestErrorCodes
    : Array.isArray(details.request_error_codes)
      ? details.request_error_codes
      : []

  let hint = ''
  if (requestCodes.includes('invalid_customer_data')) {
    hint = 'Revisa los datos del comprador y valida que la tarjeta este habilitada para compras internacionales.'
  } else if (requestCodes.includes('not_enough_funds')) {
    hint = 'La tarjeta fue rechazada por fondos insuficientes.'
  }

  return {
    message,
    requestCodes,
    joinedCodes: requestCodes.length ? requestCodes.join(',') : '',
    hint,
  }
}

export function construirDatosCheckoutCliente({ nombre, correo, telefono }) {
  const nombreNormalizado = String(nombre || '').trim()
  const correoNormalizado = String(correo || '').trim()
  const telefonoNormalizado = String(telefono || '').trim()

  const segmentosNombre = nombreNormalizado.split(/\s+/).filter(Boolean)
  const firstName = segmentosNombre[0] || 'Cliente'
  const lastName = segmentosNombre.slice(1).join(' ') || 'Tickets'

  return {
    email: correoNormalizado || undefined,
    phone: telefonoNormalizado ? { number: telefonoNormalizado } : undefined,
    name: {
      firstName,
      lastName,
    },
  }
}

export function construirDatosConfirmacion({ pedidoBase, pago, supportWhatsappFallback }) {
  const order = pago?.order || null
  const referenciaOrden = String(order?.referencia || pedidoBase?.referencia || '').trim()
  const totalOrden = Number(order?.total)
  const subtotalBase = Number(pedidoBase?.subtotal || 0)

  return {
    id:
      Number.isInteger(Number(order?.id)) && Number(order?.id) > 0
        ? Number(order?.id)
        : Number.isInteger(Number(pedidoBase?.id)) && Number(pedidoBase?.id) > 0
          ? Number(pedidoBase?.id)
          : null,
    referencia: referenciaOrden,
    nombre: String(pedidoBase?.nombre || '').trim(),
    email: String(pedidoBase?.email || '').trim(),
    telefono: String(pedidoBase?.telefono || '').trim(),
    pais: String(pedidoBase?.pais || '').trim(),
    cc: String(pedidoBase?.cc || '').trim(),
    subtotal: Number.isFinite(totalOrden) && totalOrden > 0 ? totalOrden : subtotalBase,
    currency: String(order?.currency || pedidoBase?.currency || 'USD').trim().toUpperCase() || 'USD',
    paymentId: String(pago?.paymentId || pedidoBase?.paymentId || '').trim(),
    paymentStatus: String(pago?.status || pedidoBase?.paymentStatus || '').trim().toLowerCase(),
    checkout: pago?.checkout || pedidoBase?.checkout || null,
    kyc: pago?.kyc || pedidoBase?.kyc || null,
    failureReason: pago?.failureReason || pedidoBase?.failureReason || null,
    supportWhatsapp: String(
      pago?.support?.whatsappNumber || pedidoBase?.supportWhatsapp || supportWhatsappFallback || ''
    ).replace(/\D/g, ''),
    updatedAt: String(pago?.updatedAt || pedidoBase?.updatedAt || '').trim(),
  }
}
