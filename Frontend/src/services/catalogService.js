import { API_CONFIG, CACHE_CONFIG } from '../config/constants'
import { getOrSetCached, clearCacheByPrefix } from '../utils/requestCache'
import { getSdkClient } from './sdkClient'

const CACHE_KEYS = {
  products: 'catalog:products',
  categories: (productId) => `catalog:categories:${productId}`,
}

function normalizeListResponse(value) {
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.items)) return value.items
  if (Array.isArray(value?.results)) return value.results
  if (Array.isArray(value?.data)) return value.data
  return []
}

function toPlainObject(value) {
  if (!value || typeof value !== 'object') return {}
  return { ...value }
}

function normalizeProductItem(value) {
  const product = toPlainObject(value)
  product.imagen = toAbsoluteImageUrl(product.imagen)

  if (Array.isArray(product.categorias)) {
    product.categorias = product.categorias.map((categoria) => toPlainObject(categoria))
  } else {
    product.categorias = []
  }

  return product
}

function toAbsoluteImageUrl(value) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  if (/^https?:\/\//i.test(raw) || raw.startsWith('data:')) return raw

  const base = String(API_CONFIG.baseURL || '').replace(/\/+$/, '')
  if (!base) return raw
  if (raw.startsWith('/')) return `${base}${raw}`
  return `${base}/${raw.replace(/^\/+/, '')}`
}

export async function fetchProducts() {
  return getOrSetCached({
    key: CACHE_KEYS.products,
    ttlMs: CACHE_CONFIG.productsTtlMs,
    fetcher: async () => {
      const sdk = getSdkClient()
      const response = await sdk.productos.list({
        skip: 0,
        limit: 500,
        only_active: true,
      })

      const items = normalizeListResponse(response)
      return items
        .map((item) => normalizeProductItem(item))
        .filter((item) => item.is_active !== false)
    },
  })
}

export async function fetchCategoriesByProduct(productId) {
  return getOrSetCached({
    key: CACHE_KEYS.categories(productId),
    ttlMs: CACHE_CONFIG.categoriesTtlMs,
    fetcher: async () => {
      const sdk = getSdkClient()
      const response = await sdk.categorias.list({ productoId: productId, onlyActive: true })
      return normalizeListResponse(response).map((categoria) => toPlainObject(categoria))
    },
  })
}

export function invalidateCatalogCache() {
  clearCacheByPrefix('catalog:')
}
