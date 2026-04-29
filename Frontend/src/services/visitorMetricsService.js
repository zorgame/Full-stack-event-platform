import { API_CONFIG } from '../config/constants'

const VISITOR_ID_STORAGE_KEY = 'tickets_visitor_id_v1'
const VISIT_ROUTE_HITS_SESSION_KEY = 'tickets_visit_route_hits_v1'
const VISIT_LAST_HIT_SESSION_KEY = 'tickets_visit_last_hit_v1'

const VISIT_ENDPOINT_PATH = '/pedidos/metricas/visitas/register'
const VISIT_GLOBAL_THROTTLE_MS = 30_000
const VISIT_PER_ROUTE_THROTTLE_MS = 10 * 60_000
const MAX_ROUTE_CACHE_ITEMS = 80

const PUBLIC_ROUTE_NAMES = new Set([
  'home',
  'ticket-categorias',
  'contacto',
  'terminos',
  'privacidad',
  'reembolsos',
])

function buildEndpointUrl() {
  const rawBase = String(API_CONFIG?.baseURL || '').trim().replace(/\/+$/, '')
  return rawBase ? `${rawBase}${VISIT_ENDPOINT_PATH}` : VISIT_ENDPOINT_PATH
}

function createRandomVisitorId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `v_${crypto.randomUUID().replace(/-/g, '')}`
  }

  const randomChunk = Math.random().toString(36).slice(2)
  return `v_${Date.now().toString(36)}${randomChunk}`
}

function getOrCreateVisitorId() {
  if (typeof window === 'undefined') return ''

  try {
    const existing = String(window.localStorage.getItem(VISITOR_ID_STORAGE_KEY) || '').trim()
    if (existing.length >= 12) return existing

    const created = createRandomVisitorId()
    window.localStorage.setItem(VISITOR_ID_STORAGE_KEY, created)
    return created
  } catch {
    return ''
  }
}

function normalizePath(rawPath) {
  const raw = String(rawPath || '/').trim()
  if (!raw) return '/'

  const pathOnly = raw.split('?', 1)[0].split('#', 1)[0]
  const prefixed = pathOnly.startsWith('/') ? pathOnly : `/${pathOnly}`
  const parts = prefixed.split('/').filter(Boolean)

  return parts.length ? `/${parts.join('/')}` : '/'
}

function readRouteHitsMap() {
  if (typeof window === 'undefined') return {}

  try {
    const raw = window.sessionStorage.getItem(VISIT_ROUTE_HITS_SESSION_KEY)
    if (!raw) return {}

    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function saveRouteHitsMap(map) {
  if (typeof window === 'undefined') return

  try {
    const items = Object.entries(map || {})
      .filter(([, ts]) => Number.isFinite(Number(ts)) && Number(ts) > 0)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
      .slice(0, MAX_ROUTE_CACHE_ITEMS)

    const compact = Object.fromEntries(items)
    window.sessionStorage.setItem(VISIT_ROUTE_HITS_SESSION_KEY, JSON.stringify(compact))
  } catch {
  }
}

function isPublicRoute(routeLike, normalizedPath, indexable) {
  if (!indexable) return false

  const routeName = String(routeLike?.name || '').trim()
  if (routeName) {
    return PUBLIC_ROUTE_NAMES.has(routeName)
  }

  if (normalizedPath === '/') return true
  return !/^\/(admin|user|login|payment)(\/|$)/.test(normalizedPath)
}

function shouldSendVisit(path) {
  if (typeof window === 'undefined') return false

  const now = Date.now()

  try {
    const lastGlobal = Number(window.sessionStorage.getItem(VISIT_LAST_HIT_SESSION_KEY) || 0)
    if (Number.isFinite(lastGlobal) && now - lastGlobal < VISIT_GLOBAL_THROTTLE_MS) {
      return false
    }

    const hitsMap = readRouteHitsMap()
    const lastRoute = Number(hitsMap[path] || 0)
    if (Number.isFinite(lastRoute) && now - lastRoute < VISIT_PER_ROUTE_THROTTLE_MS) {
      return false
    }

    hitsMap[path] = now
    saveRouteHitsMap(hitsMap)
    window.sessionStorage.setItem(VISIT_LAST_HIT_SESSION_KEY, String(now))
    return true
  } catch {
    return false
  }
}

function sendVisit(payload) {
  const endpoint = buildEndpointUrl()
  const body = JSON.stringify(payload)

  try {
    if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
      const blob = new Blob([body], { type: 'application/json' })
      if (navigator.sendBeacon(endpoint, blob)) {
        return
      }
    }
  } catch {
  }

  fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body,
    keepalive: true,
    credentials: 'omit',
  }).catch(() => {})
}

export function trackRouteVisit(routeLike, { indexable = true } = {}) {
  if (typeof window === 'undefined') return

  const path = normalizePath(routeLike?.fullPath || routeLike?.path || '/')
  if (!isPublicRoute(routeLike, path, indexable)) return
  if (!shouldSendVisit(path)) return

  const visitorId = getOrCreateVisitorId()
  if (!visitorId) return

  sendVisit({
    visitor_id: visitorId,
    path,
  })
}
