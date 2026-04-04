import { API_CONFIG, CACHE_CONFIG } from '../config/constants'
import { getOrSetCached, clearCacheByPrefix } from '../utils/requestCache'
import { getSdkClient } from './sdkClient'

const CACHE_KEYS = {
  products: 'catalog:products',
  categories: (productId) => `catalog:categories:${productId}`,
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
      const items = await sdk.productos.list()
      for (const item of items) {
        item.imagen = toAbsoluteImageUrl(item.imagen)
      }
      return items.filter((item) => item.is_active !== false)
    },
  })
}

export async function fetchCategoriesByProduct(productId) {
  return getOrSetCached({
    key: CACHE_KEYS.categories(productId),
    ttlMs: CACHE_CONFIG.categoriesTtlMs,
    fetcher: async () => {
      const sdk = getSdkClient()
      return sdk.categorias.list({ productoId: productId, onlyActive: true })
    },
  })
}

export function invalidateCatalogCache() {
  clearCacheByPrefix('catalog:')
}
