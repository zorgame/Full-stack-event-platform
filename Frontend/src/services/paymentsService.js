import { getSdkClient } from './sdkClient'
import { CONTACT_INFO } from '../config/constants'

const PAYMENT_STATUS_SUCCESS = new Set(['completed'])
const PAYMENT_STATUS_FAILURE = new Set([
  'failed',
  'payment-failed',
  'crypto-payer-insufficient-funds',
  'manual-kyc',
  'rejected-kyc',
  'cancelled',
  'canceled',
  'expired',
  'abandoned',
])
const PAYMENT_STATUS_KYC = new Set([
  'requires-kyc',
  'pending-kyc-review',
  'manual-kyc',
  'rejected-kyc',
  'requires-recipient-verification',
])
const PAYMENT_STATUS_TERMINAL = new Set([...PAYMENT_STATUS_SUCCESS, ...PAYMENT_STATUS_FAILURE])
const CROSSMINT_ONRAMP_NOT_ENABLED_PATTERNS = [
  /onramp is not yet enabled for production use in this project/i,
  /start testing in staging\.crossmint\.com/i,
  /enable production access/i,
]

function normalizePaymentStatus(value) {
  return String(value || '').trim().toLowerCase()
}

function normalizeWhatsappNumber(value) {
  return String(value || '').replace(/\D/g, '')
}

function toPositiveInteger(value) {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

function mapPaymentResponse(payload = {}) {
  const checkoutRaw = payload?.checkout
  const checkout =
    checkoutRaw && typeof checkoutRaw === 'object'
      ? {
          publicKey: String(checkoutRaw.public_key || '').trim() || null,
          session:
            checkoutRaw.session && typeof checkoutRaw.session === 'object'
              ? checkoutRaw.session
              : null,
        }
      : null

  const kycRaw = payload?.kyc
  const kyc =
    kycRaw && typeof kycRaw === 'object'
      ? {
          templateId: String(kycRaw.templateId || '').trim() || null,
          referenceId: String(kycRaw.referenceId || '').trim() || null,
          environmentId: String(kycRaw.environmentId || '').trim() || null,
        }
      : null

  const failureReasonRaw = payload?.failure_reason
  const failureReason =
    failureReasonRaw && typeof failureReasonRaw === 'object'
      ? {
          code: String(failureReasonRaw.code || '').trim() || null,
          message: String(failureReasonRaw.message || '').trim() || null,
        }
      : null

  const orderRaw = payload?.order
  const order =
    orderRaw && typeof orderRaw === 'object'
      ? {
          id: toPositiveInteger(orderRaw.id),
          referencia: String(orderRaw.referencia || '').trim(),
          estado: String(orderRaw.estado || '').trim().toLowerCase(),
          total: Number(orderRaw.total || 0),
          currency: String(orderRaw.currency || 'USD').trim().toUpperCase() || 'USD',
        }
      : null

  return {
    provider: String(payload?.provider || 'crossmint').trim().toLowerCase(),
    paymentId: String(payload?.payment_id || '').trim(),
    paymentToken: String(payload?.payment_token || '').trim(),
    status: normalizePaymentStatus(payload?.status),
    order,
    checkout,
    kyc,
    failureReason,
    support: {
      whatsappNumber: normalizeWhatsappNumber(payload?.support?.whatsapp_number),
    },
    accessCredentials:
      payload?.access_credentials && typeof payload.access_credentials === 'object'
        ? {
            email: String(payload.access_credentials.email || '').trim(),
            password: String(payload.access_credentials.password || '').trim() || null,
          }
        : null,
    updatedAt: String(payload?.updated_at || '').trim(),
    raw: payload?.raw && typeof payload.raw === 'object' ? payload.raw : null,
  }
}

function mapPaymentSyncSummary(payload = {}) {
  const mismatches = Array.isArray(payload?.mismatches)
    ? payload.mismatches.map((item) => ({
        pedidoId: toPositiveInteger(item?.pedido_id),
        referencia: String(item?.referencia || '').trim(),
        paymentId: String(item?.payment_id || '').trim(),
        estadoPedido: String(item?.estado_pedido || '').trim().toLowerCase(),
        estadoCrossmint: String(item?.estado_crossmint || '').trim().toLowerCase() || null,
        estadoObjetivo: String(item?.estado_objetivo || '').trim().toLowerCase() || null,
        reason: String(item?.reason || '').trim(),
        detail: String(item?.detail || '').trim() || null,
      }))
    : []

  return {
    provider: String(payload?.provider || 'crossmint').trim().toLowerCase(),
    providerAvailable: Boolean(payload?.provider_available),
    providerMessage: String(payload?.provider_message || '').trim() || null,
    syncOrderApplied: Boolean(payload?.sync_order_applied),
    scopeLimit: Number(payload?.scope_limit || 0),
    scannedOrders: Number(payload?.scanned_orders || 0),
    withPaymentSession: Number(payload?.with_payment_session || 0),
    withoutPaymentSession: Number(payload?.without_payment_session || 0),
    comparedOrders: Number(payload?.compared_orders || 0),
    inSync: Number(payload?.in_sync || 0),
    outOfSync: Number(payload?.out_of_sync || 0),
    providerErrors: Number(payload?.provider_errors || 0),
    updatedAt: String(payload?.updated_at || '').trim(),
    mismatches,
  }
}

export function isPaymentStatusSuccessful(status) {
  return PAYMENT_STATUS_SUCCESS.has(normalizePaymentStatus(status))
}

export function isPaymentStatusFailed(status) {
  return PAYMENT_STATUS_FAILURE.has(normalizePaymentStatus(status))
}

export function isPaymentStatusTerminal(status) {
  return PAYMENT_STATUS_TERMINAL.has(normalizePaymentStatus(status))
}

export function requiresPaymentKyc(status) {
  return PAYMENT_STATUS_KYC.has(normalizePaymentStatus(status))
}

function collectErrorMessages(error) {
  const candidates = [
    error?.data?.detail?.message,
    error?.data?.detail?.details?.message,
    error?.data?.detail?.details?.error,
    error?.data?.detail?.details?.detail,
    error?.data?.message,
    error?.data?.detail,
    error?.message,
  ]

  if (Array.isArray(error?.data?.detail?.details?.errors)) {
    for (const item of error.data.detail.details.errors) {
      if (typeof item === 'string') {
        candidates.push(item)
      } else if (item && typeof item === 'object') {
        candidates.push(item.message, item.error, item.detail)
      }
    }
  }

  return candidates
    .filter((value) => typeof value === 'string')
    .map((value) => value.trim())
    .filter(Boolean)
}

function isCrossmintOnrampNotEnabled(error) {
  const messages = collectErrorMessages(error)
  return messages.some((message) =>
    CROSSMINT_ONRAMP_NOT_ENABLED_PATTERNS.some((pattern) => pattern.test(message))
  )
}

function buildOnrampUnavailableMessage() {
  const whatsapp = String(CONTACT_INFO.whatsappDisplay || CONTACT_INFO.whatsappDigits || '').trim()
  if (whatsapp) {
    return `La pasarela de pago no se encuentra habilitada temporalmente. Por favor, comunicate con nuestro canal de WhatsApp (${whatsapp}); estara disponible muy pronto.`
  }

  return 'La pasarela de pago no se encuentra habilitada temporalmente. Por favor, comunicate con nuestro canal de WhatsApp; estara disponible muy pronto.'
}

export function extractPaymentErrorMessage(error, fallback = 'No fue posible procesar el pago.') {
  if (isCrossmintOnrampNotEnabled(error)) {
    return buildOnrampUnavailableMessage()
  }

  const nestedMessage =
    error?.data?.detail?.message ||
    error?.data?.detail?.details?.message ||
    error?.data?.message ||
    error?.data?.detail ||
    error?.message

  const message = typeof nestedMessage === 'string' ? nestedMessage.trim() : ''
  return message || fallback
}

export function formatPaymentStatusLabel(status) {
  const normalized = normalizePaymentStatus(status)
  if (!normalized) return 'Pendiente'

  const labels = {
    'awaiting-payment': 'Esperando pago',
    completed: 'Pagado',
    failed: 'Fallido',
    'payment-failed': 'Pago rechazado',
    'requires-kyc': 'KYC requerido',
    'pending-kyc-review': 'KYC en revision',
    'manual-kyc': 'KYC manual',
    'rejected-kyc': 'KYC rechazado',
    'requires-recipient-verification': 'Verificacion requerida',
    'crypto-payer-insufficient-funds': 'Fondos insuficientes',
  }

  return labels[normalized] || normalized.replace(/-/g, ' ')
}

export async function crearPagoPedido({ pedidoId, referencia, aceptaTerminos }) {
  const id = toPositiveInteger(pedidoId)
  if (!id) {
    throw new Error('pedidoId es invalido')
  }

  const referenciaNormalizada = String(referencia || '').trim()
  if (!referenciaNormalizada) {
    throw new Error('referencia es requerida')
  }

  if (!aceptaTerminos) {
    throw new Error('Debes aceptar los términos y condiciones para continuar.')
  }

  const sdk = getSdkClient()
  const payload = {
    pedido_id: id,
    referencia: referenciaNormalizada,
    acepta_terminos: true,
  }

  const response = await sdk.payments.create(payload)
  return mapPaymentResponse(response)
}

export async function obtenerEstadoPago({ paymentId, pedidoId = null, referencia = null, syncOrder = true }) {
  const id = String(paymentId || '').trim()
  if (!id) {
    throw new Error('paymentId es requerido')
  }

  const options = {
    sync_order: Boolean(syncOrder),
  }

  const parsedPedidoId = toPositiveInteger(pedidoId)
  if (parsedPedidoId) {
    options.pedido_id = parsedPedidoId
  }

  const referenciaNormalizada = String(referencia || '').trim()
  if (referenciaNormalizada) {
    options.referencia = referenciaNormalizada
  }

  const sdk = getSdkClient()
  const response = await sdk.payments.get(id, options)
  return mapPaymentResponse(response)
}

export async function obtenerEstadoPagoPorToken({ paymentToken, syncOrder = true }) {
  const token = String(paymentToken || '').trim()
  if (!token) {
    throw new Error('paymentToken es requerido')
  }

  const sdk = getSdkClient()
  const response = await sdk.payments.getByToken(token, {
    sync_order: Boolean(syncOrder),
  })
  return mapPaymentResponse(response)
}

export async function obtenerResumenSincronizacionPagos({ limit = 50, syncOrder = false } = {}) {
  const sdk = getSdkClient()
  const parsedLimit = Number(limit)
  const safeLimit = Number.isInteger(parsedLimit) ? Math.min(Math.max(parsedLimit, 1), 100) : 50

  const response = await sdk.payments.getSyncSummary({
    limit: safeLimit,
    sync_order: Boolean(syncOrder),
  })

  return mapPaymentSyncSummary(response)
}
