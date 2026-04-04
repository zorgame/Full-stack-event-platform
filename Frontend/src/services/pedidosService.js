import { getSdkClient } from './sdkClient'
import { clearCacheByPrefix, clearCacheKey, getOrSetCached } from '../utils/requestCache'

export const ESTADOS_PEDIDO_ADMIN = {
  pendiente: 'pendiente',
  aceptado: 'pagado',
  rechazado: 'cancelado',
}

const METRICAS_CACHE_PREFIX = 'admin:pedidos-metricas:'
const METRICAS_CACHE_TTL_MS = 90_000

function normalizeStringList(values) {
  const source = Array.isArray(values)
    ? values
    : String(values || '')
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

function normalizeNumberList(values) {
  const source = Array.isArray(values)
    ? values
    : String(values || '')
        .split(',')
        .map((item) => item.trim())

  const unique = []
  const seen = new Set()

  for (const item of source) {
    const parsed = Number(item)
    if (!Number.isInteger(parsed) || parsed <= 0 || seen.has(parsed)) continue
    seen.add(parsed)
    unique.push(parsed)
  }

  return unique
}

function toNullablePositiveNumber(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null
}

function normalizeMetricsFilters(filters = {}) {
  const estados = normalizeStringList(filters.estado)
  const paises = normalizeStringList(filters.pais)
  const producto_ids = normalizeNumberList(filters.producto_ids)
  const categoria_ids = normalizeNumberList(filters.categoria_ids)
  const topN = Number(filters.top_n)

  return {
    rango: String(filters.rango || '30d').toLowerCase(),
    fecha_desde: filters.fecha_desde || undefined,
    fecha_hasta: filters.fecha_hasta || undefined,
    group_by: String(filters.group_by || 'day').toLowerCase(),
    estado: estados,
    pais: paises,
    producto_ids,
    categoria_ids,
    min_total: toNullablePositiveNumber(filters.min_total),
    max_total: toNullablePositiveNumber(filters.max_total),
    top_n: Number.isInteger(topN) && topN > 0 ? topN : 8,
    ventas_solo_aprobadas: filters.ventas_solo_aprobadas !== false,
  }
}

function buildMetricsCacheKey(filters) {
  const payload = {
    ...filters,
    estado: [...(filters.estado || [])].sort(),
    pais: [...(filters.pais || [])].sort(),
    producto_ids: [...(filters.producto_ids || [])].sort((a, b) => a - b),
    categoria_ids: [...(filters.categoria_ids || [])].sort((a, b) => a - b),
  }

  return `${METRICAS_CACHE_PREFIX}${JSON.stringify(payload)}`
}

export async function crearPedidoCompra(payload) {
  const sdk = getSdkClient()

  const pedido = {
    correo_electronico: String(payload.correo_electronico || '').trim(),
    nombre_completo: String(payload.nombre_completo || '').trim(),
    telefono: String(payload.telefono || '').trim(),
    pais: String(payload.pais || '').trim(),
    documento: String(payload.documento || '').trim(),
    acepta_terminos: Boolean(payload.acepta_terminos),
    detalles: Array.isArray(payload.detalles)
      ? payload.detalles.map((detalle) => ({
          categoria_id: Number(detalle.categoria_id),
          cantidad: Number(detalle.cantidad),
        }))
      : [],
  }

  const created = await sdk.pedidos.create(pedido)
  clearCacheByPrefix(METRICAS_CACHE_PREFIX)
  return created
}

export async function listarPedidosAdmin(options = {}) {
  const sdk = getSdkClient()
  const skip = Number.isInteger(Number(options.skip)) ? Number(options.skip) : 0
  const limit = Number.isInteger(Number(options.limit)) ? Number(options.limit) : 200
  const estado = String(options.estado || '').trim().toLowerCase()
  return sdk.pedidos.list({
    skip,
    limit,
    estado: estado || undefined,
  })
}

export async function actualizarEstadoPedidoAdmin({ pedidoId, estado, usuarioId = null }) {
  const sdk = getSdkClient()
  const idPedido = Number(pedidoId)
  const payload = {
    estado: String(estado || '').trim().toLowerCase(),
  }

  const idUsuario = Number(usuarioId)
  if (Number.isInteger(idUsuario) && idUsuario > 0) {
    payload.usuario_id = idUsuario
  }

  const updated = await sdk.pedidos.updateEstado(idPedido, payload)
  clearCacheByPrefix(METRICAS_CACHE_PREFIX)
  return updated
}

export async function obtenerMetricasPedidosAdmin(filters = {}, { force = false } = {}) {
  const sdk = getSdkClient()
  const normalized = normalizeMetricsFilters(filters)
  const key = buildMetricsCacheKey(normalized)

  if (force) {
    clearCacheKey(key)
  }

  return getOrSetCached({
    key,
    ttlMs: METRICAS_CACHE_TTL_MS,
    fetcher: () => sdk.pedidos.metrics(normalized),
  })
}

export function limpiarCacheMetricasPedidos() {
  clearCacheByPrefix(METRICAS_CACHE_PREFIX)
}
